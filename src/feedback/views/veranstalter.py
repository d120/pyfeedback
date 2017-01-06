from django.views.decorators.http import require_safe
from django.contrib import auth
from feedback.models import Veranstaltung
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django import forms
from django.shortcuts import render_to_response
from formtools.wizard.views import SessionWizardView


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

VERANSTALTER_VIEW_TEMPLATES = {
    "veranstalter_evaluation": "formtools/wizard/veranstalter_evaluation.html",
    "veranstalter_basisinformationen": "formtools/wizard/veranstalter_basiserfassung.html",
    "veranstalter_zusammenfassung": "formtools/wizard/veranstalter_zusammenfassung.html"}


class VeranstalterEvaluationForm(forms.Form):
    veranstaltung_evaluieren = forms.BooleanField(label="Soll die Veranstaltung evaluiert werden?")


class VeranstalterBasisForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)


class VeranstalterZusammenfassungForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)


class VeranstalterWizard(SessionWizardView):
    # TODO: Login und bestellung_erlaubt beachten
    form_list = [
        ('veranstalter_evaluation', VeranstalterEvaluationForm),
        ('veranstalter_basisinformationen', VeranstalterBasisForm),
        ('veranstalter_zusammenfassung', VeranstalterZusammenfassungForm)
    ]

    def get_context_data(self, form, **kwargs):
        context = super(VeranstalterWizard, self).get_context_data(form=form, **kwargs)
        context.update({'veranstaltung': Veranstaltung.objects.get(id=self.request.session['vid'])})
        return context

    def get_template_names(self):
        print self.steps.current
        return [VERANSTALTER_VIEW_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        return render_to_response('formtools/wizard/veranstalter_evaluation.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })



