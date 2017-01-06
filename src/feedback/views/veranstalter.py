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

VERANSTALTER_VIEW_TEMPLATES = {"veranstalter_basis": "formtools/wizard/basis_erfassung.html",
             "veranstalter_basis2": "formtools/wizard/basis_erfassung2.html"}


class VeranstalterBasisForm(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()


class VeranstalterBasisForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)


class ContactWizard(SessionWizardView):
    form_list = [
        ('veranstalter_basis', VeranstalterBasisForm),
        ('veranstalter_basis2', VeranstalterBasisForm2)
    ]

    def get_template_names(self):
        print self.steps.current
        return [VERANSTALTER_VIEW_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        return render_to_response('done.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })



