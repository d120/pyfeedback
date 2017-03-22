# coding=utf-8

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin

from feedback.parser import vv as vv_parser
from feedback.models import Veranstaltung, Person, Semester, ImportCategory, ImportVeranstaltung
from feedback.models.base import FachgebietEmail
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

        category_tree = ImportCategory.objects.all().prefetch_related('ivs')
        if category_tree:  # prufen, ob die Liste leer ist
            data['vv'] = category_tree[1:]  # erste root-Kategorie ignorieren

            remaining_close_tags = ImportCategory.objects.all().aggregate(sum_lvl=Sum('rel_level'))
            if remaining_close_tags['sum_lvl'] is None:
                data['remaining_close_tags'] = 0
            else:
                data['remaining_close_tags'] = remaining_close_tags['sum_lvl']
            return render(request, 'intern/import_vv_edit.html', data)
        else:
            messages.error(request, 'Bevor zu importierende Veranstaltungen ausgewählt werden ' +
                           'können, muss zunächst eine VV-XML-Datei hochgeladen werden.')
            return HttpResponseRedirect(reverse('import_vv'))
    else:
        # gewählte Veranstaltungen übernehmen und Personen zuordnen

        # Liste der ausgewählten Veranstaltungen holen
        v_str = [ele[1] for ele in request.POST.lists() if ele[0] == 'v']
        if not len(v_str):
            messages.warning(request, 'Es wurden keine Veranstaltungen für den Import ausgewählt!')
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
                v = Veranstaltung.objects.create(typ=iv.typ, name=iv.name, status=Veranstaltung.STATUS_ANGELEGT, semester=semester,
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


class PersonFormView(UserPassesTestMixin, ListView):
    model = Person
    template_name = 'intern/import_vv_edit_users.html'
    context_object_name = 'persons'

    def get_queryset(self):
        return Person.persons_to_edit()

    def test_func(self):
        return self.request.user.is_superuser


class PersonFormUpdateView(UserPassesTestMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = 'intern/import_vv_edit_users_update.html'

    def get_id(self):
        try:
            next_id = Person.persons_to_edit().filter(id__gt=self.object.id).order_by("id")[0].id
        except (Person.DoesNotExist, IndexError):
            next_id = None
        try:
            prev_id = Person.persons_to_edit().filter(id__lt=self.object.id).order_by("-id")[0].id
        except (Person.DoesNotExist, IndexError):
            prev_id = None

        return next_id, prev_id

    def form_valid(self, form):
        p = form.save(commit=False)
        p.geschlecht = form.cleaned_data['geschlecht']
        p.email = form.cleaned_data['email']
        p.fachgebiet = FachgebietEmail.get_fachgebiet_from_email(p.email)
        p.save()
        messages.success(self.request, 'Benutzerdatensätze wurden erfolgreich gespeichert.')

        if p.fachgebiet is not None:
            messages.success(self.request, ' '.join((p.full_name(), ' wurde dem Fachbereich ', str(p.fachgebiet), ' zugewiesen.')).encode('utf-8'))

        return super(PersonFormUpdateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Das Feld für die Anrede oder Email ist leer.')
        return super(PersonFormUpdateView, self).form_invalid(form)

    def get_success_url(self):
        next_id, prev_id = self.get_id()
        if next_id:
            return reverse('import_vv_edit_users_update', args=[next_id])
        else:
            return reverse('import_vv_edit_users')

    def test_func(self):
        return self.request.user.is_superuser

    def has_similar_name(self):
        vorname = self.object.vorname.split(' ')[0]
        nachname = self.object.nachname
        similar_persons = Person.persons_with_similar_names(vorname, nachname)

        if similar_persons.exists():
            if self.object == similar_persons.get():
                return False
            else:
                return similar_persons.count() > 0


class SimilarNamesView(UserPassesTestMixin, DetailView):
    model = Person
    template_name = 'intern/import_vv_edit_users_namecheck.html'
    context_object_name = 'person_new'

    def post(self, request, *args, **kwargs):
        id_old = request.POST['id_old']
        id_new = request.POST['id_new']

        old_person = Person.objects.get(pk=id_old)
        new_person = Person.objects.get(pk=id_new)

        Person.replace_veranstalter(new_person, old_person)
        if not Person.is_veranstalter(new_person):
            new_person.delete()

        return HttpResponseRedirect(reverse('import_vv_edit_users'))

    def get_context_data(self, **kwargs):
        context = super(SimilarNamesView, self).get_context_data(**kwargs)
        context['new_vorname'] = self.object.vorname
        context['new_nachname'] = self.object.nachname

        vorname = context['new_vorname'].split(' ')[0]
        nachname = context['new_nachname']

        context['similar_person'] = Person.persons_with_similar_names(vorname, nachname)
        context['old_veranstaltungen'] = Person.veranstaltungen(context['similar_person'])
        context['new_veranstaltungen'] = Person.veranstaltungen(context['person_new'])
        return context

    def test_func(self):
        return self.request.user.is_superuser
