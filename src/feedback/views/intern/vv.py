# coding=utf-8

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Q, Sum
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin

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


class PersonFormView(UserPassesTestMixin, FormView):
    template_name = 'intern/import_vv_edit_users.html'
    form_class = PersonForm

    def get(self, request, *args, **kwargs):
        person_form_set = formset_factory(PersonForm, extra=0)
        context = self.get_context_data()
        is_missing = Q(geschlecht='') | Q(email='')
        pers = Person.objects.filter(is_missing, veranstaltung__semester=Semester.current()).order_by('id').distinct()

        formset = person_form_set(initial=[{'anrede': p.geschlecht, 'name': p.full_name(), 'id': p.id, 'email': p.email}
                                           for p in pers])
        context['formset'] = formset
        return self.render_to_response(context)

    def test_func(self):
        return self.request.user.is_superuser


class PersonFormUpdateView(UserPassesTestMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = 'intern/import_vv_edit_users_update.html'

    def get_next_id(self):
        try:
            next_person = Person.objects.filter(id__gt=self.object.id, geschlecht='', email='').order_by("id")[0:1].get().id
        except Person.DoesNotExist:
            next_person = -1
        return next_person

    def get_prev_id(self):
        try:
            prev_person = Person.objects.filter(id__lt=self.object.id, geschlecht='', email='').order_by("-id")[0:1].get().id
        except Person.DoesNotExist:
            prev_person = -1
        return prev_person

    def get_to_edit_count(self):
        return Person.objects.filter(geschlecht='', email='').count()

    def form_valid(self, form):
        p = form.save(commit=False)
        p.geschlecht = form.cleaned_data['geschlecht']
        p.email = form.cleaned_data['email']
        p.save()
        messages.success(self.request, u'Benutzerdatensätze wurden erfolgreich gespeichert.')
        return super(PersonFormUpdateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, u'Das Feld für die Anrede oder Email ist leer.')
        return super(PersonFormUpdateView, self).form_invalid(form)

    def get_success_url(self):
        next_id = self.get_next_id()
        if next_id > 0:
            return reverse('import_vv_edit_users_update', args=[next_id])
        else:
            return reverse('import_vv_edit_users')

    def test_func(self):
        return self.request.user.is_superuser
