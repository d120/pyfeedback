# coding=utf-8

from django.test import TestCase

from feedback.models import Person, Veranstaltung, Semester, Kommentar
from feedback.forms import BestellungModelForm, KommentarModelForm


class BestellungModelFormTest(TestCase):
    def setUp(self):
        self.p = []
        self.p.append(Person.objects.create(vorname='Eric', nachname='Idle'))
        self.p.append(Person.objects.create(vorname='John', nachname='Cleese'))
        self.s = Semester.objects.create(semester=20120)
        self.v = Veranstaltung.objects.create(typ='v', name='Life of Brian', semester=self.s,
                                              evaluieren=True, grundstudium=False)
        self.v.veranstalter.add(self.p[0])

        """Alle benötigten Felder wenn an der Evaluation teilgenommen wird mit einem Beispiel"""
        self.fullFormExample = {'anzahl': 100,
                                'sprache': 'de',
                                'verantwortlich': self.p[0].id, }

    def test_init(self):
        with self.assertRaises(KeyError):
            BestellungModelForm()

        form = BestellungModelForm(instance=self.v)
        self.assertItemsEqual(form.fields['verantwortlich'].queryset.all(), (self.p[0],))

    def test_evaluate_leere_bestellung(self):
        """Veranstaltung nimmt an der Evaluation teil. Es werden keine weiteren Felder übertragen"""
        form_data = {'evaluieren': 'on'}
        form = BestellungModelForm(instance=self.v, data=form_data)
        self.assertFalse(form.is_valid(), 'Form wurde als valide evaluiert obwohl Anzahl etc fehlen')

    def test_evaluieren_null_boegen_bestellung(self):
        """Veranstaltng nimmt an der Evaluation teil. Es werden aber 0 Bögen bestellt"""
        form_Data = self.fullFormExample
        form_Data.update({'evaluieren': 'on'})
        form_Data['anzahl'] = 0

        form = BestellungModelForm(instance=self.v, data=form_Data)
        self.assertFalse(form.is_valid(), 'Es wurden 0 Bögen bestellt, trotzdem ist die Bestellung gültig')

    def test_evaluate_partiel_complete_bestellung(self):
        """Veranstaltung nimmt an der Evaluation teil. Es werden nicht alle benötigen Daten übertragen. Alle Kombinationen werden getestet"""
        requiredFields = self.fullFormExample

        # ja es gibt 2^n - 2 kombinationen!
        iterationEnd = pow(2, len(requiredFields)) - 1
        noBits = len(requiredFields) + 2  # +2 für '0b'
        binFormat = "#0%db" % noBits

        for i in range(1, iterationEnd):
            # Wir nehmen immer an der Evaluation teil
            formData = {'evaluieren': 'on'}
            # Die aktuelle Auswahl als nBit String
            selection = format(i, binFormat).split('b')[1]

            # Teste das die Anzahl der Bits immer gleich der Felder ist
            self.assertEqual(len(requiredFields), len(selection),
                             'Die Anzahl Bits stimmt nicht mit der Anzahl der Felder überein')

            # iterriere über die Zeichen im String
            for bitNumber in range(0, len(requiredFields)):
                # Wenn das Bit gesetzt ist
                if selection[bitNumber] == '1':
                    # füge das Feld zum Form hinzu
                    formData.update({requiredFields.keys()[bitNumber]: requiredFields.values()[bitNumber]})

            form = BestellungModelForm(instance=self.v, data=formData)
            self.assertFalse(form.is_valid(),
                             'Form ist valide obwohl nicht alle Felder gesetzt sind. Daten: %s' % str(formData))

    def test_evaluieren_bestellung(self):
        """Veranstaltung nimmt an der Evalution teil. Es werden alle nötigen Daten angegeben"""
        form_data = self.fullFormExample
        form_data.update({'evaluieren': 'on', 'typ': 'vu', 'ergebnis_empfaenger': [self.p[0].id]})
        form = BestellungModelForm(instance=self.v, data=form_data)

        self.assertTrue(form.is_valid(),
                        'Form wurde als invalide evaluiert obwohl alle nötigen Felder angegeben sind. Prüfen ob wirklich alle nötigen Felder angegeben sind')

    def test_nicht_evaluieren_bestellung(self):
        """Veranstaltung nimmt nicht an der Evaluation teil. Jede Bestellung ist gültig."""
        # Aktuell wird eine nicht auswahl von evaluieren mit nicht übertragen
        # des Feldes dargestellt. Darum werden einfach keine Daten übertragen
        form_data = {'typ': 'vu'}
        form = BestellungModelForm(instance=self.v, data=form_data)

        self.assertTrue(form.is_valid(),
                        'Veranstaltung nimmt nicht an der Evaluation teil. Trotzdem ist das Form ungültig')


class KommentarModelFormTest(TestCase):
    def setUp(self):
        self.p = []
        self.p.append(Person.objects.create(vorname='Eric', nachname='Idle'))
        self.p.append(Person.objects.create(vorname='John', nachname='Cleese'))
        self.s = Semester.objects.create(semester=20120)
        self.v = Veranstaltung.objects.create(typ='v', name='Life of Brian', semester=self.s,
                                              evaluieren=True, grundstudium=False)
        self.v.veranstalter.add(self.p[0])
        self.k = Kommentar.objects.create(veranstaltung=self.v, autor=self.p[0], text='Great!')

    def test_init(self):
        with self.assertRaises(KeyError):
            KommentarModelForm(instance=self.k)

        forms = []
        forms.append(KommentarModelForm(veranstaltung=self.v))
        forms.append(KommentarModelForm(instance=self.k, veranstaltung=self.v))
        for f in forms:
            self.assertItemsEqual(f.fields['autor'].queryset.all(), (self.p[0],))
