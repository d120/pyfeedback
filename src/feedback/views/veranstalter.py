# coding=utf-8

from django import forms
from django.conf import settings
from django.views.decorators.http import require_safe
from django.contrib import auth
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string

from formtools.wizard.views import SessionWizardView
from feedback.models import Veranstaltung, Tutor, past_semester_orders, Log
from feedback.forms import VeranstaltungEvaluationForm, VeranstaltungBasisdatenForm, \
    VeranstaltungFreieFragen, VeranstaltungVeroeffentlichung, VeranstaltungDigitaleEvaluationForm


@require_safe
def login(request):
    if 'vid' in request.GET and 'token' in request.GET:
        vid = int(request.GET['vid'])
        token = str(request.GET['token'])

        user = auth.authenticate(vid=vid, token=token)
        if user:
            auth.login(request, user)
            v = Veranstaltung.objects.get(id=vid)
            request.session['vid'] = v.id
            request.session['veranstaltung'] = str(v)

            return HttpResponseRedirect(reverse('veranstalter-index'))

    return render(request, 'veranstalter/login_failed.html')


def veranstalter_dashboard(request):
    """Definiert den Dashboard für die Veranstalter-View."""
    if request.user.username != settings.USERNAME_VERANSTALTER:
        return render(request, 'veranstalter/not_authenticated.html')

    data = {}
    veranst = Veranstaltung.objects.get(id=request.session['vid'])

    data["veranstaltung"] = veranst
    data["logs"] = Log.objects.filter(veranstaltung=veranst).order_by('timestamp')
    data["allow_order"] = veranst.allow_order()

    if veranst.status >= Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR:
        bestellung = [("Evaluieren", veranst.get_evaluieren_display)]
        if veranst.evaluieren:
            bestellung.append(("Typ", veranst.get_typ_display))
            bestellung.append(("Anazhl", veranst.anzahl))
            bestellung.append(("Sprache", veranst.get_sprache_display))
            bestellung.append(("Verantwortlich", veranst.verantwortlich.__str__() + '\n'
                               + veranst.verantwortlich.anschrift + '\n'
                               + veranst.verantwortlich.email))

            ergebnis_empfanger_str = ""
            for empfaenger in veranst.ergebnis_empfaenger.all():
                ergebnis_empfanger_str += empfaenger.__str__() + "\n"
            bestellung.append(("Ergebnis Empfänger", ergebnis_empfanger_str))

            if veranst.auswertungstermin:
                bestellung.append(("Auswertungstermin", veranst.auswertungstermin))

            bestellung.append(("Primärdozent", veranst.primaerdozent))
            bestellung.append(("Freie Frage 1", veranst.freiefrage1))
            bestellung.append(("Freie Frage 2", veranst.freiefrage2))
            bestellung.append(("Veröffentlichen", veranst.get_veroeffentlichen_display))

        data["bestellung"] = bestellung

    return render(request, 'veranstalter/dashboard.html', data)


# ---------------------------------------- START WIZARD ---------------------------------------- #

# Alle Templates, die vom Wizard gebraucht werden.
VERANSTALTER_VIEW_TEMPLATES = {
    "evaluation": "formtools/wizard/evaluation.html",
    "basisdaten": "formtools/wizard/basisdaten.html",
    "digitale_eval": "formtools/wizard/digitale_evaluation.html",
    "freie_fragen": "formtools/wizard/freiefragen.html",
    "veroeffentlichen": "formtools/wizard/veroeffentlichen.html",
    "zusammenfassung": "formtools/wizard/zusammenfassung.html"
}

# Alle Schritte, die vom Wizard gebraucht werden.
VERANSTALTER_WIZARD_STEPS = {
    "evaluation": "Evaluation",
    "basisdaten": "Basisdaten",
    "digitale_eval": "Digitale Evaluation",
    "freie_fragen": "Freie Fragen",
    "veroeffentlichen": "Veroeffentlichen",
    "zusammenfassung": "Zusammenfassung"
}


def perform_evalution(wizard):
    """
    Wenn wir keine Vollerhebung haben, und der Veranstalter nicht evauliert, dann
    springt der Wizard direkt zur Zusammenfassung.
    """
    if not wizard.cached_obj.get("cleaned_data_evaluation", {}):
        wizard.cached_obj["cleaned_data_evaluation"] = wizard.get_cleaned_data_for_step('evaluation') or {}
    cleaned_data = wizard.cached_obj["cleaned_data_evaluation"]

    v = wizard.get_instance()

    if v.semester.vollerhebung:
        return True

    return cleaned_data.get('evaluieren', True)

def show_digital_eval_form(wizard):
    show_summary_form = perform_evalution(wizard)
    if show_summary_form:
        cleaned_data = wizard.get_cleaned_basisdaten()
        digitale_eval = cleaned_data.get('digitale_eval', '')
        return digitale_eval
    return show_summary_form


def swap(collection, i, j):
    """Einfache Swap-Funktion, die für die Darstellung von Daten in der Zusammenfassung gebraucht wird."""
    # swap elements of summary data and ignore IndexError of no evaluation
    try:
        collection[i], collection[j] = collection[j], collection[i]
    except IndexError:
        pass


class VeranstalterWizard(SessionWizardView):
    """Definiert den Wizard für den Bestellprozess."""
    form_list = [
        ('evaluation', VeranstaltungEvaluationForm),
        ('basisdaten', VeranstaltungBasisdatenForm),
        ('digitale_eval', VeranstaltungDigitaleEvaluationForm),
        ('freie_fragen', VeranstaltungFreieFragen),
        ('veroeffentlichen', VeranstaltungVeroeffentlichung),
        ('zusammenfassung', forms.Form)
    ]

    condition_dict = {
        'basisdaten': perform_evalution,
        'digitale_eval': show_digital_eval_form,
        'freie_fragen': perform_evalution,
        'veroeffentlichen': perform_evalution,
    }

    cached_obj = {}

    def dispatch(self, request, *args, **kwargs):
        self.cached_obj = {}
        return super(VeranstalterWizard, self).dispatch(request, *args, **kwargs)

    def get_instance(self):
        if self.cached_obj.get("veranstaltung_obj", None) is None:
            if 'vid' not in self.request.session:
                raise Http404('Ihre Session ist abgelaufen. Bitte loggen Sie sich erneut über den Link ein.')
            self.cached_obj["veranstaltung_obj"] = Veranstaltung.objects.\
                select_related().filter(id=self.request.session['vid'])[0]
        return self.cached_obj["veranstaltung_obj"]

    def get_all_veranstalter(self):
        if self.cached_obj.get("all_veranstalter", None) is None:
            self.cached_obj["all_veranstalter"] = self.get_instance().veranstalter.all()
        return self.cached_obj["all_veranstalter"]

    def get_cleaned_basisdaten(self):
        if not self.cached_obj.get("cleaned_data_basisdaten", {}):
            self.cached_obj["cleaned_data_basisdaten"] = self.get_cleaned_data_for_step('basisdaten') or {}
        return self.cached_obj["cleaned_data_basisdaten"]

    def get(self, request, *args, **kwargs):
        if self.request.user.username != settings.USERNAME_VERANSTALTER:
            return render(self.request, 'veranstalter/not_authenticated.html')
        veranstaltung = self.get_instance()
        if veranstaltung.allow_order():
            return super(VeranstalterWizard, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('veranstalter-index'))

    def get_context_data(self, form, **kwargs):
        context = super(VeranstalterWizard, self).get_context_data(form=form, **kwargs)
        context.update({'veranstaltung': self.get_instance()})

        progressbar = []
        step_active = True
        for step_key in self.get_form_list():
            progressbar.append({
                'step_value': VERANSTALTER_WIZARD_STEPS[step_key],
                'step_active': step_active,
                'step_key': step_key if step_key in self.steps.all else None
            })
            if step_active:
                if step_key == self.steps.current:
                    step_active = False
        context.update({'progressbar': progressbar})

        if self.steps.current == "basisdaten":
            past_sem_data = past_semester_orders(self.get_instance())
            context.update({'past_semester_data': past_sem_data})

        if self.steps.current == "zusammenfassung":
            all_form_data = []
            for step_form in self.get_form_list():
                form_obj = self.get_form(
                    step=step_form,
                    data=self.storage.get_step_data(step_form),
                    files=self.storage.get_step_files(step_form),
                )

                if form_obj.is_valid():
                    for field_key, field_obj in list(form_obj.fields.items()):
                        cleaned_d = form_obj.cleaned_data[field_key]
                        field_value = ""

                        if isinstance(field_obj, forms.fields.TypedChoiceField):
                            for key, choice in field_obj.choices:
                                if key == cleaned_d:
                                    field_value = choice
                                    break
                        else:
                            field_value = form_obj.cleaned_data[field_key]

                        field_label = field_obj.label

                        if field_label is None:
                            field_label = field_key

                        all_form_data.append({
                            'label': field_label,
                            'value': field_value
                        })

            swap(all_form_data, 5, 6)
            swap(all_form_data, 6, 7)
            context.update({'all_form_data':  all_form_data})
        return context

    def get_form_instance(self, step):
        return self.get_instance()

    def get_form_kwargs(self, step=None):
        kwargs = super(VeranstalterWizard, self).get_form_kwargs(step)

        if step == "basisdaten":
            kwargs.update({'all_veranstalter': self.get_all_veranstalter()})
            
        return kwargs

    def get_template_names(self):
        return [VERANSTALTER_VIEW_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        cleaned_data = {}
        if perform_evalution(self) :
            # django-formtools uses get_form_list to get steps, which are added when their method in condition_dict is True
            # get_cleaned_basisdaten uses step 'basisdaten', which is not added to steps if perform_evalution is False
            cleaned_data = self.get_cleaned_basisdaten()
        ergebnis_empfaenger = cleaned_data.get('ergebnis_empfaenger', None)

        instance = self.get_instance()

        save_to_db(self.request, instance, form_list)
        context = self.get_context_data('zusammenfassung')
        send_mail_to_verantwortliche(ergebnis_empfaenger, context, instance)

        return render(request=None, template_name='formtools/wizard/bestellung_done.html', )



def send_mail_to_verantwortliche(ergebnis_empfaenger, context, veranstaltung):
    """
    Sendet eine Email an die Ergebnis-Empfaenger mit der Zusammenfassung der Bestellung.
    :param ergebnis_empfaenger: Empfänger der Ergebnisse
    :param context: E-Mail Inhalt
    :param veranstaltung: Veranstaltung
    """
    context.update({'veranstaltung': veranstaltung})

    msg_html = render_to_string('formtools/wizard/email_zusammenfassung.html', context)

    if ergebnis_empfaenger is not None:
        for e in ergebnis_empfaenger:
            send_mail(
                'Evaluation der Lehrveranstaltungen - Zusammenfassung der Daten für {}'.format(veranstaltung.name),
                'Nachfolgend finder Sie Informationen zu Ihrer Bestellung',
                settings.DEFAULT_FROM_EMAIL,
                [e.email],
                html_message=msg_html,
                fail_silently=False,
            )


def save_to_db(request, instance, form_list):
    """
    Speichert alle eingegebenen Daten des Wizards auf das Modell
    und setzt den Status einer Veranstaltung auf den nächsten validen Zustand.
    :param request: aktueller Request
    :param instance: die aktuelle Instanz
    :param form_list: Liste aller Forms
    """
    for form in form_list:
        for key, val in form.cleaned_data.items():
            if isinstance(form.instance, Veranstaltung):
                if key == 'ergebnis_empfaenger':
                    getattr(instance, key).set(val)
                else:
                    setattr(instance, key, val)
            else:
                setattr(form.instance, key, val)

        if hasattr(form, 'instance') and not isinstance(form.instance, Veranstaltung):
            form.instance.save()

    instance.set_next_state()
    instance.save()
    instance.log(request.user, is_frontend=True)
