# coding=utf-8

from typing import Any
from django import forms
from django.forms import widgets

from feedback.models import Person, Veranstaltung, Kommentar, BarcodeScannEvent
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from feedback.models import Semester, Mailvorlage


class BestellWizardForm(forms.ModelForm):
    required_css_class = "required"


class VeranstaltungAnzahlForm(BestellWizardForm) :
    """Defines form for number of orders"""

    class Meta:
        model = Veranstaltung
        fields = ("anzahl",)
    
    def __init__(self, *args, **kwargs) :
        super(VeranstaltungAnzahlForm, self).__init__(*args, **kwargs)

        self.fields["anzahl"] = forms.IntegerField(label=_("Anzahl der Teilnehmende"), min_value=0)


class VeranstaltungEvaluationForm(BestellWizardForm):
    """Definiert die Form für den 1. Schritt des Wizards"""

    class Meta:
        model = Veranstaltung
        fields = ("evaluieren",)
        widgets = {"evaluieren": forms.RadioSelect()}

    def __init__(self, *args, **kwargs):
        hide_field = kwargs.pop('hide_eval_field', False)

        super(VeranstaltungEvaluationForm, self).__init__(
            *args, **dict(kwargs, initial={"evaluieren": "True"})
        )

        self.fields['evaluieren'].required = True
        
        if hide_field :
            # with vollerhebung and correct anzahl hide field so no option not to evaluate
            self.fields['evaluieren'].widget = forms.HiddenInput()
class VeranstaltungBasisdatenForm(BestellWizardForm):
    """Definiert die Form für den 2. Schritt des Wizards."""

    def __init__(self, *args, **kwargs):
        veranstalter_queryset = kwargs.pop("all_veranstalter", None)

        super(VeranstaltungBasisdatenForm, self).__init__(*args, **kwargs)

        # Schränke QuerySet nur auf den Veranstalter ein
        self.fields["ergebnis_empfaenger"].queryset = veranstalter_queryset

        self.fields["auswertungstermin"] = forms.DateField(
            label=_("Auswertungstermin"),
            help_text=_("Zu diesem Termin werden die Ergebnisse versandt. Nach diesem Datum können keine Evaluationsbögen mehr abgegeben werden und die digitale Evaluation geschlossen."),
            widget=forms.DateInput(attrs={"type": "date", "value": Semester.current().standard_ergebnisversand}),
        )

        # Lösche die Auswahl ob es eine Übung gibt wenn es keine Vorlesung ist
        vltypes = ["vu", "v"]
        if kwargs["instance"].typ not in vltypes:
            del self.fields["typ"]
        else:
            choices = []
            for cur in self.fields["typ"].choices:
                if cur[0] in vltypes:
                    choices.append(cur)

            self.fields["typ"].choices = choices

        # Wenn Evaluation oder Vollerhebung, dann sind alle anderen Felder notwendig
        for k, field in list(self.fields.items()):
            if k not in ["auswertungstermin"]:
                field.required = True

    class Meta:
        model = Veranstaltung
        fields = (
            "typ",
            "sprache",
            "ergebnis_empfaenger",
            "auswertungstermin",
        )
        widgets = {"ergebnis_empfaenger": forms.CheckboxSelectMultiple}
    
    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        
        # "digitale_eval" and "verantwortlich" removed from user interface
        cleaned_data["digitale_eval"] = True

        if "ergebnis_empfaenger" in cleaned_data :
            # because it does not validate yet, django doesn't notice that "ergebnis_empfaenger" does not exist and this causes error
            cleaned_data["verantwortlich"] = cleaned_data["ergebnis_empfaenger"][0]


class VeranstaltungDigitaleEvaluationForm(BestellWizardForm):
    class Meta:
        model = Veranstaltung
        fields = ("digitale_eval_type", )

class VeranstaltungFreieFragen(BestellWizardForm):
    """Definiert die Form für den 5. Schritt des Wizards."""

    class Meta:
        model = Veranstaltung
        fields = ("freiefrage1", "freiefrage2")

class VeranstaltungVeroeffentlichung(BestellWizardForm):
    """Definiert die Form für den 7. Schritt des Wizards."""

    class Meta:
        model = Veranstaltung
        fields = ("veroeffentlichen",)


class UploadFileForm(forms.Form):
    """Definiert die Form für den XML Import."""
    file = forms.FileField(label=_("Datei"))


class PersonForm(forms.ModelForm):
    """Definiert die Form für die Bearbeitung von Personen."""

    class Meta:
        model = Person
        fields = ("geschlecht", "email")

    def clean(self):
        geschlecht = self.cleaned_data.get("geschlecht")
        email = self.cleaned_data.get("email")

        if not geschlecht or not email:
            raise forms.ValidationError(_("Das Feld für die Anrede oder Email ist leer."))


class PersonUpdateForm(forms.ModelForm):
    """Definiert die Form für die Nachpflege von Personendaten"""

    class Meta:
        model = Person
        fields = ("anschrift", "fachgebiet")


class KommentarModelForm(forms.ModelForm):
    """Definiert die Form für Kommentare."""

    def __init__(self, *args, **kwargs):
        veranst = kwargs.pop("veranstaltung", None)

        if veranst is None:
            raise KeyError(
                "This form needs an veranstaltung=... parameter to function properly."
            )

        super(KommentarModelForm, self).__init__(*args, **kwargs)
        self.fields["autor"].queryset = veranst.veranstalter.all()

    class Meta:
        model = Kommentar
        exclude = ("veranstaltung",)


CLOSE_ORDER_CHOICES = (("ja", _("Ja")), ("nein", _("Nein")))


class CloseOrderForm(forms.Form):
    """Definiert die Form für das Beenden der Bestellphase"""
    auswahl = forms.ChoiceField(choices=CLOSE_ORDER_CHOICES, label=_("Auswahl"))


class CreateBarcodeScannEventForm(forms.ModelForm):
    """Definiert die Form für einen Barcodescan-Event"""
    scanner_token = forms.CharField()

    class Meta:
        model = BarcodeScannEvent
        fields = ["barcode", "scanner"]

    def clean(self):
        super(CreateBarcodeScannEventForm, self).clean()
        cd = self.cleaned_data

        if cd["scanner"].token != cd["scanner_token"]:
            raise ValidationError(
                ValidationError("Token dose not match", code="tokendmatch")
            )
        else:
            barcode_decoded = Veranstaltung.decode_barcode(cd["barcode"])
            cd["veranstaltung"] = barcode_decoded["veranstaltung"]

            if barcode_decoded["tutorgroup"] >= 1:
                cd["tutorgroup"] = barcode_decoded["tutorgroup"]

        return cd


class UploadTANCSV(forms.Form):
    csv = forms.FileField(label=_('CSV Datei aus Evasys'), help_text=_('Im Evasysseitenmenü unter dem Punkt "Teilnahmeübersicht" generierbar.'))

class SendOrPDF(forms.Form):
    choice = forms.ChoiceField(choices=(('mail', _('Versende TANs per E-Mail'),),), label=_('Verarbeitungsart'))

class EMailTemplates(forms.Form):
    losungstemplate = forms.ModelChoiceField(Mailvorlage.objects.all(), 
    required=False, help_text=_('Hier wird eine E-Mail an alle Veranstalter*innen ohne Anhang versendet. Es werden die selben Ersetzungen wie beim Standardmailsystem unterstützt und zusätzlich das Feld {{ losung }}.'))
    tantemplate = forms.ModelChoiceField(Mailvorlage.objects.all(), required=False, help_text=_('Hier wird die gewählte Vorlage an alle Veranstalter*innen mit einer CSV Datei versendet. Es werden die selben Ersetzungen wie beim Standardmailsystem unterstützt.'))