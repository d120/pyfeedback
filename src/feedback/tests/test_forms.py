# coding=utf-8

from django.test import TestCase

from feedback.models import Person, Veranstaltung, Semester, Kommentar
from feedback.forms import KommentarModelForm


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
