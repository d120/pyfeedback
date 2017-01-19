# coding=utf-8

from django import forms
from django.forms import extras

from feedback.models import Person, Veranstaltung, Kommentar, BarcodeScanner, BarcodeScannEvent
from django.core.exceptions import ValidationError


class VeranstaltungEvaluationForm(forms.ModelForm):
    class Meta:
        model = Veranstaltung
        fields = ('evaluieren',)


class VeranstaltungBasisdatenForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VeranstaltungBasisdatenForm, self).__init__(*args, **kwargs)

        # Schränke QuerySet nur auf den Veranstalter ein
        veranstalter_queryset = kwargs['instance'].veranstalter.all()
        self.fields['verantwortlich'].queryset = veranstalter_queryset
        self.fields['ergebnis_empfaenger'].queryset = veranstalter_queryset

        # Keine negative Anzahl möglich
        self.fields['anzahl'] = forms.IntegerField(min_value=1)

        # Nutze ein Widget bei dem nur das jahr des letzten Auswertungstermins angegeben werden kann
        years_tuple = kwargs['instance'].semester.auswertungstermin_years()
        self.fields['auswertungstermin'].widget = extras.SelectDateWidget(years=years_tuple)

        # Auswertungstermin kann nur gewählt werden wenn es ein Seminar oder Praktikum ist
        if kwargs['instance'].typ not in ['se', 'pr']:
            del self.fields['auswertungstermin']

        # Lösche die Auswahl ob es eine Übung gibt wenn es keine Vorlesung ist
        vltypes = ['vu', 'v']
        if kwargs['instance'].typ not in vltypes:
            del self.fields['typ']
        else:
            choices = []
            for cur in self.fields['typ'].choices:
                if cur[0] in vltypes:
                    choices.append(cur)

            self.fields['typ'].choices = choices

        # Wenn Evaluation oder Vollerhebung, dann sind alle anderen Felder notwendig
        for k, field in self.fields.items():
            field.required = True

    class Meta:
        model = Veranstaltung
        fields = ('typ', 'anzahl', 'sprache', 'verantwortlich', 'ergebnis_empfaenger', 'auswertungstermin')
        widgets = {'ergebnis_empfaenger': forms.CheckboxSelectMultiple,
                   'auswertungstermin': forms.SelectDateWidget}


class VeranstaltungPrimaerDozentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs.pop("is_dynamic_form", False):
            super(VeranstaltungPrimaerDozentForm, self).__init__(*args, **kwargs)
        else:
            previous_step_data = kwargs.pop('basisdaten', None)
            super(VeranstaltungPrimaerDozentForm, self).__init__(*args, **kwargs)
            if previous_step_data is not None:
                self.fields['primaerdozent'].queryset = previous_step_data['ergebnis_empfaenger']
                self.fields['primaerdozent'].required = True

    class Meta:
        model = Veranstaltung
        fields = ('primaerdozent',)


class VeranstaltungDozentDatenForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('email', 'anschrift')


class VeranstaltungFreieFragen(forms.ModelForm):
    class Meta:
        model = Veranstaltung
        fields = ('freiefrage1', 'freiefrage2')


class VeranstaltungTutorenForm(forms.Form):
    csv_tutoren = forms.CharField(label='CSV', widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        preset_csv = kwargs.pop("preset_csv", None)
        super(VeranstaltungTutorenForm, self).__init__(*args, **kwargs)
        self.fields["csv_tutoren"].initial = preset_csv


class UploadFileForm(forms.Form):
    file = forms.FileField(label='Datei')


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('geschlecht', 'email')

    def clean(self):
        geschlecht = self.cleaned_data.get('geschlecht')
        email = self.cleaned_data.get('email')

        if not geschlecht or not email:
            raise forms.ValidationError('Das Feld für die Anrede oder Email ist leer.')


class KommentarModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        veranst = kwargs.pop('veranstaltung', None)

        if veranst is None:
            raise KeyError(u'This form needs an veranstaltung=... parameter to function properly.')

        super(KommentarModelForm, self).__init__(*args, **kwargs)
        self.fields['autor'].queryset = veranst.veranstalter.all()

    class Meta:
        model = Kommentar
        exclude = ('veranstaltung',)


class PersonUpdateForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('anschrift', 'fachgebiet')


# class VeranstaltungFreiFragenForm(forms.ModelForm):
#     class Meta:
#         model = Veranstaltung
#         fields = ('freiefrage1', 'freiefrage2')


# class VeranstaltungKleingruppenForm(forms.ModelForm):
#     class Meta:
#         model = Veranstaltung
#         fields = ('kleingruppen',)


class CreateBarcodeScannEventForm(forms.ModelForm):
    """Handelt die erste haelfte von Barcode scanns"""
    scanner_token = forms.CharField()

    class Meta:
        model = BarcodeScannEvent
        fields = ['barcode', 'scanner']

    def clean(self):
        super(CreateBarcodeScannEventForm, self).clean()
        cd = self.cleaned_data

        if cd['scanner'].token != cd['scanner_token']:
            raise ValidationError(ValidationError('Token dose not match', code='tokendmatch'))
        else:
            barcode_decoded = Veranstaltung.decode_barcode(cd['barcode'])
            cd['veranstaltung'] = barcode_decoded['veranstaltung']

            if (barcode_decoded['tutorgroup'] >= 1):
                cd['tutorgroup'] = barcode_decoded['tutorgroup']

        return cd
