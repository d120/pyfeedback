# coding=utf-8

from django import forms
from django.conf import settings
from django.views.decorators.http import require_safe
from django.contrib import auth
from django.http import HttpRequest, HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from formtools.wizard.views import SessionWizardView
from feedback.models import Veranstaltung, Tutor, past_semester_orders, Log
from feedback.forms import VeranstaltungEvaluationForm, VeranstaltungBasisdatenForm, \
    VeranstaltungFreieFragen, VeranstaltungVeroeffentlichung, VeranstaltungDigitaleEvaluationForm, VeranstaltungAnzahlForm


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

            return HttpResponseRedirect(reverse('feedback:veranstalter-index'))

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
        bestellung = [(_("Evaluieren"), veranst.get_evaluieren_display)]
        if veranst.evaluieren:
            bestellung.append((_("Typ"), veranst.get_typ_display))
            bestellung.append((_("Anazhl"), veranst.anzahl))
            bestellung.append((_("Sprache"), veranst.get_sprache_display))
            bestellung.append((_("Verantwortlich"), veranst.verantwortlich.__str__() + '\n'
                               + veranst.verantwortlich.anschrift + '\n'
                               + veranst.verantwortlich.email))

            ergebnis_empfanger_str = ""
            for empfaenger in veranst.ergebnis_empfaenger.all():
                ergebnis_empfanger_str += empfaenger.__str__() + "\n"
            bestellung.append((_("Ergebnis Empfänger"), ergebnis_empfanger_str))

            if veranst.auswertungstermin:
                bestellung.append((_("Auswertungstermin"), veranst.auswertungstermin))

            bestellung.append((_("Primärdozent"), veranst.primaerdozent))
            bestellung.append((_("Freie Frage 1"), veranst.freiefrage1))
            bestellung.append((_("Freie Frage 2"), veranst.freiefrage2))
            bestellung.append((_("Veröffentlichen"), veranst.get_veroeffentlichen_display))

        data["bestellung"] = bestellung

    return render(request, 'veranstalter/dashboard.html', data)


# ---------------------------------------- START WIZARD ---------------------------------------- #

# Alle Templates, die vom Wizard gebraucht werden.
VERANSTALTER_VIEW_TEMPLATES = {
    "anzahl" : "formtools/wizard/anzahl.html",
    "evaluation": "formtools/wizard/evaluation.html",
    "basisdaten": "formtools/wizard/basisdaten.html",
    "digitale_eval": "formtools/wizard/digitale_evaluation.html",
    "freie_fragen": "formtools/wizard/freiefragen.html",
    "veroeffentlichen": "formtools/wizard/veroeffentlichen.html",
    "zusammenfassung": "formtools/wizard/zusammenfassung.html"
}

# Alle Schritte, die vom Wizard gebraucht werden.
VERANSTALTER_WIZARD_STEPS = {
    "anzahl" : _("Anzahl"),
    "evaluation": _("Evaluation"),
    "basisdaten": _("Basisdaten"),
    "digitale_eval": _("Digitale Evaluation"),
    "freie_fragen": _("Freie Fragen"),
    "veroeffentlichen": _("Veroeffentlichen"),
    "zusammenfassung": _("Zusammenfassung")
}


def perform_evalution(wizard):
    """
    Checks if user has choosen to evaluate, default returns True
    """
    wizard.cached_obj["cleaned_data_evaluation"] = wizard.get_cleaned_data_for_step('evaluation') or {}
    cleaned_data = wizard.cached_obj["cleaned_data_evaluation"]

    return cleaned_data.get('evaluieren', True)

def vollerhebung_check(wizard) :
    """
    Checks if the semester is a vollerhebung semester
    """
    v = wizard.get_instance()

    return v.semester.vollerhebung

def order_amount_check(wizard) :
    """
    Checks if amount of orders greater than or equal to MIN_BESTELLUNG_ANZAHL
    """
    wizard.cached_obj["cleaned_data_anzahl"] = wizard.get_cleaned_data_for_step('anzahl') or {}
    cleaned_data = wizard.cached_obj["cleaned_data_anzahl"]

    return cleaned_data.get('anzahl', 0) >= Veranstaltung.MIN_BESTELLUNG_ANZAHL

def activate_step(wizard, step) :
    """
    Checks if given step should be shown in the form
    """
    vollerhebung = vollerhebung_check(wizard)
    amount = order_amount_check(wizard)
    evaluation = perform_evalution(wizard)

    if step == "basisdaten" :
        return (evaluation or vollerhebung) and amount
    elif step == "digitale_eval" :
        return (evaluation or vollerhebung) and amount
    elif step == "freie_fragen" :
        return (evaluation or vollerhebung) and amount
    elif step == "veroeffentlichen" :
        return (evaluation or vollerhebung) and amount
    
    return True

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
        ('anzahl', VeranstaltungAnzahlForm),
        ('evaluation', VeranstaltungEvaluationForm),
        ('basisdaten', VeranstaltungBasisdatenForm),
        ('digitale_eval', VeranstaltungDigitaleEvaluationForm),
        ('freie_fragen', VeranstaltungFreieFragen),
        ('veroeffentlichen', VeranstaltungVeroeffentlichung),
        ('zusammenfassung', forms.Form)
    ]

    condition_dict = {
        'basisdaten': lambda wizard : activate_step(wizard, 'basisdaten'),
        'digitale_eval': lambda wizard : activate_step(wizard, 'digitale_eval'),
        'freie_fragen': lambda wizard : activate_step(wizard, 'freie_fragen'),
        'veroeffentlichen': lambda wizard : activate_step(wizard, 'veroeffentlichen'),
    }

    cached_obj = {}

    def process_step(self, form):
        step = self.steps.current
        request = self.request

        if step == 'anzahl' :
            anzahl_data = form.cleaned_data.get('anzahl', 0)
            if anzahl_data < Veranstaltung.MIN_BESTELLUNG_ANZAHL :
                messages.info(request, Veranstaltung.anzahl_too_few_msg())

        elif step == 'evaluation' :
            if not order_amount_check(self) :
                messages.error(self.request, Veranstaltung.anzahl_too_few_msg())

        return super().process_step(form)
    
    def dispatch(self, request, *args, **kwargs):
        self.cached_obj = {}
        return super(VeranstalterWizard, self).dispatch(request, *args, **kwargs)

    def get_instance(self):
        if self.cached_obj.get("veranstaltung_obj", None) is None:
            if 'vid' not in self.request.session:
                raise Http404(_('Ihre Session ist abgelaufen. Bitte loggen Sie sich erneut über den Link ein.'))
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
            return HttpResponseRedirect(reverse('feedback:veranstalter-index'))

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
        if step == 'anzahl' :
            # don't show help text when vollerhebung
            kwargs.update({'vollerhebung' : vollerhebung_check(self)})

        elif step == 'evaluation' :
            if not order_amount_check(self) :
                # anzahl less than MIN_BESTELLUNG_ANZAHL, so no evaluaiton
                kwargs.update({'hide_eval_field': True})
                kwargs.update({'no_eval' : True})

            elif vollerhebung_check(self) and order_amount_check(self) :
                # vollerhebung with correct anzahl, so always evaluate
                kwargs.update({'hide_eval_field': True})

        elif step == "basisdaten":
            kwargs.update({'all_veranstalter': self.get_all_veranstalter()})
            
        return kwargs

    def get_template_names(self):
        return [VERANSTALTER_VIEW_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        cleaned_data = {}
        if activate_step(self, 'basisdaten') :
            # django-formtools uses get_form_list to get steps, which are added when their method in condition_dict is True
            # get_cleaned_basisdaten uses step 'basisdaten', which is not added to steps if activate_step at step basisdaten is False
            cleaned_data = self.get_cleaned_basisdaten()
        ergebnis_empfaenger = cleaned_data.get('ergebnis_empfaenger', None)

        instance = self.get_instance()

        save_to_db(self.request, instance, form_list)
        context = self.get_context_data('zusammenfassung')
        send_mail_to_verantwortliche(ergebnis_empfaenger, context, instance)

        return render(request=self.request, template_name='formtools/wizard/bestellung_done.html', )



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
                _('Evaluation der Lehrveranstaltungen - Zusammenfassung der Daten für {name}').format(name=veranstaltung.name),
                _('Nachfolgend finder Sie Informationen zu Ihrer Bestellung'),
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
