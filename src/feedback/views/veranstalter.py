# coding=utf-8

from django.conf import settings
from django.contrib import messages
from django.contrib import auth
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_safe, require_http_methods

from feedback.forms import BestellungModelForm, KommentarModelForm, PersonUpdateForm, VeranstaltungFreiFragenForm, \
    VeranstaltungKleingruppenForm
from feedback.models import Veranstaltung, Person, Einstellung, Kommentar, past_semester_orders
from django.views.generic.edit import UpdateView
from django.views.generic.detail import DetailView
from django.shortcuts import redirect


@require_safe
def login(request):
    if 'vid' in request.GET and 'token' in request.GET:
        vid = int(request.GET['vid'])
        token = unicode(request.GET['token'])

        user = auth.authenticate(vid=vid, token=token)
        if user:
            auth.login(request, user)
            v = Veranstaltung.objects.get(id=vid)
            request.session['vid'] = v.id
            request.session['veranstaltung'] = unicode(v)
            return HttpResponseRedirect(reverse('veranstalter-index'))

    return render(request, 'veranstalter/login_failed.html')


@require_http_methods(['GET', 'HEAD', 'POST'])
def index(request):
    if request.user.username != settings.USERNAME_VERANSTALTER:
        return render(request, 'veranstalter/not_authenticated.html')

    data = {}
    veranst = Veranstaltung.objects.get(id=request.session['vid'])

    # TODO: statt Betrachtung der Sichtbarkeit automatisch aktuelles Semester (-> Kalender) annehmen
    if veranst.semester.sichtbarkeit == 'ADM' and Einstellung.get('bestellung_erlaubt') == '1':
        if request.method == 'POST':
            order_form = BestellungModelForm(request.POST, instance=veranst)
            if order_form.is_valid():
                order_form.save()
                return redirect('VerantwortlicherUpdate')
        else:
            order_form = BestellungModelForm(instance=veranst)
        data['order_form'] = order_form
        data['paper_dict'] = past_semester_orders(veranst)

    if veranst.semester.sichtbarkeit != 'ADM':
        try:
            kommentar = Kommentar.objects.get(veranstaltung=veranst)
        except Kommentar.DoesNotExist:
            kommentar = None

        if request.method == 'POST':
            comment_form = KommentarModelForm(request.POST, instance=kommentar, veranstaltung=veranst)
            if comment_form.is_valid():
                # TODO: löschen ermöglichen
                kommentar = comment_form.save(commit=False)
                kommentar.veranstaltung = veranst
                kommentar.save()
                messages.success(request, 'Ihre Änderungen wurden gespeichert.')
        else:
            comment_form = KommentarModelForm(instance=kommentar, veranstaltung=veranst)
        data['comment_form'] = comment_form

    data['veranstaltung'] = veranst
    return render(request, 'veranstalter/index.html', data)


class VerantwortlicherUpdate(UpdateView):
    model = Person
    form_class = PersonUpdateForm
    success_url = reverse_lazy('FreieFragenUpdate')

    def get_context_data(self, **kwargs):
        context = super(VerantwortlicherUpdate, self).get_context_data(**kwargs)
        try:
            context['veranstaltung'] = Veranstaltung.objects.get(id=self.request.session['vid'])
        except Exception:
            pass
        return context

    def get_object(self):
        try:
            veranst = Veranstaltung.objects.get(id=self.request.session['vid'])
            return Person.objects.get(pk=veranst.verantwortlich.pk)
        except Exception:
            pass


class FreieFragenUpdate(UpdateView):
    model = Veranstaltung
    form_class = VeranstaltungFreiFragenForm
    template_name = 'feedback/veranstaltung_freie_fragen_form.html'
    success_url = reverse_lazy('KleingruppenUpdate')

    def get_context_data(self, **kwargs):
        context = super(FreieFragenUpdate, self).get_context_data(**kwargs)
        try:
            context['veranstaltung'] = Veranstaltung.objects.get(id=self.request.session['vid'])
        except Exception:
            pass
        return context

    def get_object(self):
        try:
            return Veranstaltung.objects.get(id=self.request.session['vid'])
        except Exception:
            pass


class KleingruppenUpdate(UpdateView):
    model = Veranstaltung
    form_class = VeranstaltungKleingruppenForm
    template_name = 'feedback/veranstaltung_kleingruppen.html'
    success_url = reverse_lazy('VeranstaltungZusammenfassung')

    def dispatch(self, request, *args, **kwargs):
        # Wenn die Veranstaltung keine Übung hat leite weiter auf die Zusammenfassung
        try:
            veranst = Veranstaltung.objects.get(id=request.session['vid'])
            if veranst.has_uebung() == False:
                # FIXME: redirect to overview
                return redirect('VeranstaltungZusammenfassung')
            else:
                return super(KleingruppenUpdate, self).dispatch(request, *args, **kwargs)
        except Exception:
            pass

    def get_context_data(self, **kwargs):
        context = super(KleingruppenUpdate, self).get_context_data(**kwargs)
        try:
            context['veranstaltung'] = Veranstaltung.objects.get(id=self.request.session['vid'])
        except Exception:
            pass
        return context

    def get_object(self):
        try:
            return Veranstaltung.objects.get(id=self.request.session['vid'])
        except Exception:
            pass


class VeranstaltungZusammenfassung(DetailView):
    model = Veranstaltung
    template_name = 'feedback/veranstaltung_zusamenfassung.html'

    def get_object(self):
        try:
            return Veranstaltung.objects.get(id=self.request.session['vid'])
        except Exception:
            pass
