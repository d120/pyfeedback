# coding=utf-8

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Q
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from feedback.parser import vv as vv_parser
from feedback.models import Veranstaltung, Person, Semester, ImportCategory, ImportVeranstaltung
from feedback.forms import PersonForm, UploadFileForm


# TODO: durch FormView ersetzen
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def import_vv(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # TODO: Fehlerbehandlung
            vv_parser.parse_vv_xml(request.FILES['file'])
            return HttpResponseRedirect(reverse('import_vv_edit'))
        else:
            messages.error(request, 'Fehler beim Upload')
    else:
        form = UploadFileForm()
    return render(request, 'intern/import_vv.html', {'form': form})


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def import_vv_edit(request):
    data = {}

    if request.method in ('HEAD', 'GET'):
        # VV zur Auswahl von Vorlesungen anzeigen
        data['semester'] = Semester.objects.all()
        try:
            data['vv'] = ImportCategory.objects.get(parent=None)
        except ImportCategory.DoesNotExist:
            messages.error(request, 'Bevor zu importierende Veranstaltungen ausgewählt werden ' +
                           'können, muss zunächst eine VV-XML-Datei hochgeladen werden.')
            return HttpResponseRedirect(reverse('import_vv'))
        return render(request, 'intern/import_vv_edit.html', data)

    else:
        # gewählte Veranstaltungen übernehmen und Personen zuordnen

        # Liste der ausgewählten Veranstaltungen holen
        v_str = [ele[1] for ele in request.POST.lists() if ele[0] == 'v']
        if not len(v_str):
            messages.warning(request, u'Es wurden keine Veranstaltungen für den Import ausgewählt!')
            return HttpResponseRedirect(reverse('import_vv_edit'))
        v_ids = [int(ele) for ele in v_str[0]]  # IDs von unicode nach int konvertieren

        # ausgewähltes Semester holen
        try:
            semester = Semester.objects.get(semester=request.POST['semester'])
        except (Semester.DoesNotExist, KeyError):
            return HttpResponseRedirect(reverse('import_vv_edit'))

        # Veranstaltungen übernehmen
        data['v'] = []
        for iv in ImportVeranstaltung.objects.filter(id__in=v_ids):
            try:
                v = Veranstaltung.objects.create(typ=iv.typ, name=iv.name, semester=semester,
                                                 lv_nr=iv.lv_nr, grundstudium=False, evaluieren=True)
            except IntegrityError:
                # Veranstaltung wurde bereits importiert (kann vorkommen, wenn sie im VV in
                # mehreren Kategorien vorkommt)
                continue

            # Accounts für Veranstalter erstellen, falls nötig
            for ip in iv.veranstalter.all():
                p = Person.create_from_import_person(ip)
                v.veranstalter.add(p)

        # temporäre Daten löschen
        vv_parser.parse_vv_clear()
        return HttpResponseRedirect(reverse('import_vv_edit_users'))


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def import_vv_edit_users(request):
    data = {}
    person_form_set = formset_factory(PersonForm, extra=0)

    # Personen suchen, die eine Veranstaltung im aktuellen Semester und unvollständige Daten haben
    has_missing_data = Q(geschlecht='') | Q(email='')
    pers = Person.objects.filter(has_missing_data, veranstaltung__semester=Semester.current())
    pers = pers.distinct()

    if request.method == 'POST':
        formset = person_form_set(request.POST)
        personen = request.POST['personen']

        # TODO: im else-Fall werden keine Namen angezeigt, da sie auf initial basieren
        # TODO: vollständige Einträge speichern, auch wenn andere Fehler haben
        successful_saves = 0
        for form, pid in zip(formset.forms, personen.split(',')):
            if form.is_valid():
                p = pers.get(id=pid)
                p.geschlecht = form.cleaned_data['anrede']
                p.email = form.cleaned_data['email']
                p.save()
                successful_saves += 1

        messages.success(request, u'%i Benutzerdatensätze wurden erfolgreich gespeichert.' % successful_saves)
        if successful_saves > 0:
            return HttpResponseRedirect(reverse('intern-index'))

    else:
        # Formulare erzeugen
        personen = ','.join([str(p.id) for p in pers])
        formset = person_form_set(initial=[{
                                             'anrede': p.geschlecht,
                                             'name': p.full_name(),
                                             'adminlink':
                                                 request.build_absolute_uri(
                                                     reverse('admin:feedback_person_change', args=(p.id,))),
                                             'email': p.email
                                         } for p in pers])

    data['personen'] = personen
    data['formset'] = formset
    return render(request, 'intern/import_vv_edit_users.html', data)
