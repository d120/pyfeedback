from django import forms

from django.core.exceptions import ValidationError

from feedback.models import Semester, Mailvorlage, Veranstaltung

class SendMailForm(forms.Form):
    semester = forms.ModelChoiceField(queryset=Semester.objects.order_by('-semester'),
                                 label="Semester")
    recipient = forms.MultipleChoiceField(choices=Veranstaltung.STATUS_CHOICES, widget=forms.CheckboxSelectMultiple,
                                          label = "Mail senden an Veranstalter der Veranstaltung mit Bestellstatus")
    include_tutors = forms.BooleanField(required=False,
                                        label="Mail auch an die Tutoren der jeweiligen Veranstaltungen schicken?")
    mail_template = forms.ModelChoiceField(queryset=Mailvorlage.objects.all(), required=False,
                                      label="Vorlage")
    mail_subject = forms.CharField(label="Betreff", required=False)
    mail_body = forms.CharField(widget=forms.Textarea, label="Mailtext", required=False)

    def clean(self):
        super(SendMailForm, self).clean()

        mt = self.cleaned_data.get("mail_template", False)

        if 'load_template' in self.data:
            if mt:
                self.data = self.data.copy()
                self.data["mail_subject"] = mt.subject
                self.data["mail_body"] = mt.body
                self.add_error("mail_template", ValidationError("Vorlage geladen"))
            else:
                self.add_error("mail_template", ValidationError("Keine Vorlage ausgewählt"))

        return self.cleaned_data

