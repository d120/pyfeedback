# coding=utf-8

from django.conf import settings
from django.views.decorators.http import require_safe
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.shortcuts import render_to_response
from formtools.wizard.views import SessionWizardView

from feedback.models import Veranstaltung
from feedback.forms import VeranstaltungEvaluationForm, VeranstaltungBasisdatenForm, VeranstaltungPrimaerDozentForm, \
    VeranstaltungDozentDatenForm, VeranstaltungFreieFragen


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

            if v.status is Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR or Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET:
                return HttpResponseRedirect(reverse('veranstalter-index'))

    return render(request, 'veranstalter/login_failed.html')


VERANSTALTER_VIEW_TEMPLATES = {
    "evaluation": "formtools/wizard/evaluation.html",
    "basisdaten": "formtools/wizard/basisdaten.html",
    "primaerdozent": "formtools/wizard/primaerdozent.html",
    "verantwortlicher_address": "formtools/wizard/address.html",
    "freie_fragen": "formtools/wizard/freiefragen.html"
}


def perform_evalution(wizard):
    """
    Wenn wir keine Vollerhebung haben, und der Veranstalter nicht evauliert, dann
    springt der Wizard direkt zur Zusammenfassung.
    """
    cleaned_data = wizard.get_cleaned_data_for_step('evaluation') or {}
    v = Veranstaltung.objects.get(id=wizard.request.session['vid'])

    if v.semester.vollerhebung:
        return True

    return cleaned_data.get('evaluieren', True)


def show_primaerdozent_form(wizard):
    show_summary_form = perform_evalution(wizard)
    if show_summary_form:
        cleaned_data = wizard.get_cleaned_data_for_step('basisdaten') or {}
        ergebnis_empfaenger = cleaned_data.get('ergebnis_empfaenger', None)
        if ergebnis_empfaenger is not None:
            if ergebnis_empfaenger.count() == 1:
                return False

    return show_summary_form


class VeranstalterWizard(SessionWizardView):
    form_list = [
        ('evaluation', VeranstaltungEvaluationForm),
        ('basisdaten', VeranstaltungBasisdatenForm),
        ('primaerdozent', VeranstaltungPrimaerDozentForm),
        ('verantwortlicher_address', VeranstaltungDozentDatenForm),
        ('freie_fragen', VeranstaltungFreieFragen),
    ]

    condition_dict = {
        'basisdaten': perform_evalution,
        'primaerdozent': show_primaerdozent_form,
        'verantwortlicher_address': perform_evalution,
        'freie_fragen': perform_evalution,
    }

    def get_instance(self):
        return Veranstaltung.objects.get(id=self.request.session['vid'])

    def get(self, request, *args, **kwargs):
        if self.request.user.username != settings.USERNAME_VERANSTALTER:
            return render(self.request, 'veranstalter/not_authenticated.html')
        return super(VeranstalterWizard, self).get(request, *args, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super(VeranstalterWizard, self).get_context_data(form=form, **kwargs)
        context.update({'veranstaltung': self.get_instance()})
        return context

    def get_form_instance(self, step):
        if step == "verantwortlicher_address":
            basisdaten = self.get_cleaned_data_for_step('basisdaten')
            return basisdaten["verantwortlich"]
        return self.get_instance()

    def get_form_kwargs(self, step=None):
        kwargs = super(VeranstalterWizard, self).get_form_kwargs(step)
        if step == 'primaerdozent':
            basisdaten = self.get_cleaned_data_for_step('basisdaten')
            kwargs.update({'basisdaten': basisdaten})
        return kwargs

    def get_template_names(self):
        return [VERANSTALTER_VIEW_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        if not any(isinstance(x, VeranstaltungPrimaerDozentForm) for x in form_list):
            # preselect primaer dozent
            cleaned_data = self.get_cleaned_data_for_step('basisdaten') or {}
            ergebnis_empfaenger = cleaned_data.get('ergebnis_empfaenger', None)
            if ergebnis_empfaenger is not None:
                form_primar = VeranstaltungPrimaerDozentForm(is_dynamic_form=True,
                                                             data={'primaerdozent': ergebnis_empfaenger[0].id},
                                                             instance=self.get_instance())
                form_primar.is_valid()
                form_list.append(form_primar)

        form_data = process_form_data(form_list)
        instance = self.get_instance()

        save_to_db(self.request, instance, form_list)

        return render_to_response('formtools/wizard/zusammenfassung.html', {'form_data': form_data,
                                                                            'form_list': form_list})


def process_form_data(form_list):
    form_data = [form.cleaned_data for form in form_list]
    return form_data


def save_to_db(request, instance, form_list):
    """
    Speichert alle eingegebenen Daten des Wizards auf das Modell
    und setzt den Status einer Veranstaltung auf den nächsten validen Zustand
    """
    for form in form_list:
        for key, val in form.cleaned_data.iteritems():
            if isinstance(form.instance, Veranstaltung):
                setattr(instance, key, val)
            else:
                setattr(form.instance, key, val)

        if not isinstance(form.instance, Veranstaltung):
            form.instance.save()

    instance.set_next_state()
    instance.save()
    instance.log(request.user, is_frontend=True)
