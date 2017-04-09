from feedback.forms_intern import SendMailForm
from django.views.generic.edit import FormView

from django.core.exceptions import ValidationError

class SendMailView(FormView):
    template_name = 'intern/sendmail_form.html'
    form_class = SendMailForm
    success_url = 'sendet'

    def form_valid(self, form):
        return super(SendMailView, self).form_valid(form)