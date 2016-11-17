# coding=utf-8

from xml.etree import ElementTree
from django.db import IntegrityError

from feedback.models import ImportCategory, ImportVeranstaltung, ImportPerson


def parse_vv_xml(xmlfile):
    parse_vv_clear()

    # Fix &nbsp; in XML File @see http://stackoverflow.com/a/7265260
    # @see http://effbot.org/elementtree/elementtree-xmlparser.htm#tag-ET.XMLParser.entity
    parser = ElementTree.XMLParser()
    parser.parser.UseForeignDTD(True)
    parser.entity['nbsp'] = unichr(160)

    etree = ElementTree.ElementTree()

    root = etree.parse(xmlfile, parser=parser).find('CourseCatalogueArea')
    root_cat = ImportCategory.objects.create(name='root', rel_level=None)

    parse_vv_recurse(root, root_cat)


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


def parse_vv_recurse(ele, cat):
    is_new_category = True
    last_category_depth = 0
    for e in ele:
        # neue Kategorie hinzufügen
        if e.tag == 'CourseCatalogueArea':
            name = e.find('Name').text

            rel_step = last_category_depth
            if is_new_category:
                is_new_category = False
                rel_step = 1

            sub_cat = ImportCategory.objects.create(name=name, rel_level=rel_step)
            last_category_depth = parse_vv_recurse(e, sub_cat) - 1

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
            veranst = parse_instructors(e.find('InstructorString').text)
            try:
                iv = ImportVeranstaltung.objects.create(typ=typ, name=name, lv_nr=lv_nr, category=cat)
            except IntegrityError:
                continue
            iv.veranstalter = veranst
    return 0 if is_new_category else last_category_depth


def parse_instructors(instr):
    veranst = []

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
        veranst.append(ImportPerson.objects.get_or_create(vorname=vorname, nachname=nachname)[0])

    return veranst
