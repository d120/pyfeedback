# coding=utf-8

from xml.etree import ElementTree
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from feedback.models import ImportCategory, ImportVeranstaltung, ImportPerson


def replace_first_line(file, replacement):
    # suppress a type error which was confusing
    if type(file) not in (InMemoryUploadedFile, TemporaryUploadedFile):
        with open(file, 'r', encoding='iso-8859-1') as f:
            data = f.readlines()

        if "!DOCTYPE" not in data[0]:
            data[0] = replacement
            with open(file, 'w') as f:
                f.writelines(data)


def parse_vv_xml(xmlfile):
    parse_vv_clear()

    # Fix &nbsp; in XML File @see http://stackoverflow.com/a/7265260
    # @see http://effbot.org/elementtree/elementtree-xmlparser.htm#tag-ET.XMLParser.entity
    parser = ElementTree.XMLParser()
    # TODO: UseForeignDTD is not compatible with Python 3
    # parser.parser.UseForeignDTD(True)

    parser.entity['nbsp'] = chr(0x160)
    etree = ElementTree.ElementTree()

    # Workaround for the UseForeignDTD problem
    # if missing, adds DOCTYPE tag to handle &nbsp; and changes encoding to utf-8
    doctype = '''<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE CourseCatalogue [<!ENTITY nbsp "&#0160;">]>\n'''
    replace_first_line(xmlfile, doctype)

    root = etree.parse(xmlfile, parser=parser).find('CourseCatalogueArea')

    context = {
        'staged_people': set(),
        'staged_veranstaltungen': [],
    }

    with transaction.atomic():
        root_cat = ImportCategory.objects.create(parent=None, name='root', rel_level=None)

        # stage courses and people in memory
        parse_vv_recurse(root, root_cat, context)

        # flush everything to the DB in bulk
        process_bulk_inserts(context)


def parse_vv_clear():
    # alle Einträge löschen
    ImportVeranstaltung.objects.all().delete()
    ImportCategory.objects.all().delete()
    ImportPerson.objects.all().delete()


# vl=Vorlesung, vu=Vorlesung mit Übung, iv=Integrierte Veranstaltung
# TODO: eigentlich vl -> v, aber vu häufig aufgeteilt in vl + ue
_mapping_veranstaltung = {
    'vl': 'vu',
    'vu': 'vu',
    'iv': 'vu',
    'se': 'se',
    'pr': 'pr',
    'pp': 'pr',  # Projekt Praktikum auf Praktikum
    'pj': 'pr',  # Projekt auf Praktikum
    'pl': 'pr',  # Praktikum in der Lehre auf Praktikum
}


def parse_vv_recurse(ele, cat, context):
    is_new_category = True
    last_category_depth = 0
    for e in ele:
        # neue Kategorie hinzufügen
        if e.tag == 'CourseCatalogueArea':
            name = e.find('Name').text

            rel_step = last_category_depth
            if is_new_category:  # wenn eine Unterkategorie zum ersten Mal erstellt wird hat sie immer ein Step von 1
                is_new_category = False
                rel_step = 1

            sub_cat = ImportCategory.objects.create(name=name, rel_level=rel_step, parent=cat)
            last_category_depth = parse_vv_recurse(e, sub_cat, context)

        # neue Vorlesung hinzufügen
        elif e.tag == 'Course':
            lv_nr = e.find('Number').text

            # Wenn die Veranstaltung keine Nummer hat wird sie nicht evaluiert
            if lv_nr is None:
                continue

            try:
                typ = _mapping_veranstaltung[lv_nr[-2:]]
            except KeyError:
                # Veranstaltungstyp wird nicht evaluiert (kommt nicht in mapping_veranstaltung vor)
                continue

            name = e.find('Name').text

            instructor_string = e.find('InstructorString').text
            is_attended_course = (instructor_string != "N.N.")

            instructor_tuples = []
            if is_attended_course and instructor_string:
                instructor_tuples = stage_instructors(instructor_string, context)

            context['staged_veranstaltungen'].append({
                'typ': typ,
                'name': name,
                'lv_nr': lv_nr,
                'category': cat,
                'is_attended_course': is_attended_course,
                'instructors': instructor_tuples,
            })

    # Zurückgegeben wird die Rekursionstiefe der zuletzt erstellten Kategorie, oder wenn keine erstellt wurden 0
    return 0 if is_new_category else (last_category_depth - 1)


def stage_instructors(instr, context):
    tuples_list = []
    # Personen trennen
    personen = instr.strip().split('; ')
    if personen == ['']:
        return []

    for p in personen:
        # an letztem Leerzeichen trennen
        try:
            vorname, nachname = p.rsplit(' ', 1)
        except ValueError:
            vorname, nachname = '', p

        person_tuple = (vorname, nachname)
        context['staged_people'].add(person_tuple)
        tuples_list.append(person_tuple)

    return tuples_list


def process_bulk_inserts(context):
    person_instances = [ImportPerson(vorname=p[0], nachname=p[1]) for p in context['staged_people']]
    ImportPerson.objects.bulk_create(person_instances, ignore_conflicts=True)

    person_map = {
        (p.vorname, p.nachname): p.id
        for p in ImportPerson.objects.all()
    }

    course_instances = []
    for cd in context['staged_veranstaltungen']:
        course_instances.append(
            ImportVeranstaltung(
                typ=cd['typ'],
                name=cd['name'],
                lv_nr=cd['lv_nr'],
                category=cd['category'],
                is_attended_course=cd['is_attended_course']
            )
        )

    ImportVeranstaltung.objects.bulk_create(course_instances, ignore_conflicts=True)

    # fetch inserted courses and map lv_nr to a LIST of IDs
    all_lv_nrs = set(cd['lv_nr'] for cd in context['staged_veranstaltungen'])
    inserted_courses = ImportVeranstaltung.objects.filter(lv_nr__in=all_lv_nrs)

    course_map = {}
    for c in inserted_courses:
        # group all database IDs that share the same lv_nr
        course_map.setdefault(c.lv_nr, []).append(c.id)

    # create m2m relationships
    ThroughModel = ImportVeranstaltung.veranstalter.through
    m2m_instances = []
    seen_m2m = set()

    for cd in context['staged_veranstaltungen']:
        if not cd['is_attended_course']:
            continue

        course_ids = course_map.get(cd['lv_nr'], [])

        for course_id in course_ids:
            for person_tuple in cd['instructors']:
                person_id = person_map.get(person_tuple)

                if person_id:
                    m2m_key = (course_id, person_id)
                    # only add the m2m link if it hasn't been staged
                    if m2m_key not in seen_m2m:
                        seen_m2m.add(m2m_key)
                        m2m_instances.append(
                            ThroughModel(
                                importveranstaltung_id=course_id,
                                importperson_id=person_id,
                            )
                        )

    if m2m_instances:
        ThroughModel.objects.bulk_create(m2m_instances, batch_size=2000, ignore_conflicts=True)