import os
from subprocess import call

from django.test import TestCase
from django.conf import settings

from feedback.models import Semester, Person, Veranstaltung, Fragebogen2009, Mailvorlage, Einstellung
from feedback.tests.tools import NonSuTestMixin, get_veranstaltung


class GenerateLettersTest(NonSuTestMixin, TestCase):
    def _get_erhebungswoche(self):
        with open(settings.LATEX_PATH + 'erhebungswoche.inc', 'r') as f:
            return f.readline()

    def _set_erhebungswoche(self, ad):
        with open(settings.LATEX_PATH + 'erhebungswoche.inc', 'w') as f:
            return f.write(ad)

    def _delete_erhebungswoche_file(self):
        os.remove(settings.LATEX_PATH + 'erhebungswoche.inc')

    def setUp(self):
        super(GenerateLettersTest, self).setUp()
        try:
            devnull = open(os.devnull, 'w')
            if call(['which', 'pdflatex'], stdin=devnull, stdout=devnull, stderr=devnull) == 1:
                return self.skipTest("No pdflatex found")
        except OSError:
            return self.skipTest("OSError while looking for pdflatex")

        self.path = '/intern/generate_letters/'
        try:
            self.orig_contents = self._get_erhebungswoche()
        except IOError:
            pass

    def tearDown(self):
        try:
            if self.orig_contents != self._get_erhebungswoche():
                self._set_erhebungswoche(self.orig_contents)
        except AttributeError:
            self._delete_erhebungswoche_file()

    def test_get(self):
        self.do_non_su_test(self.path)
        self.client.login(username='supers', password='pw')

        response = self.client.get(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'intern/generate_letters.html')
        self.assertEqual(response.templates[0].name, 'intern/generate_letters.html')
        self.assertSequenceEqual(response.context['semester'], list(Semester.objects.all()))
        try:
            self.assertEqual(response.context['erhebungswoche'], self.orig_contents)
        except AttributeError:
            pass

    def test_post(self):
        self.client.login(username='supers', password='pw')
        s, v = get_veranstaltung('v')
        p0 = Person.objects.create(vorname='Je', nachname='Mand', email='je@ma.nd', geschlecht='w',
                                   anschrift='S202 D120')
        p1 = Person.objects.create(vorname='Noch Je', nachname='Mand', email='nochje@ma.nd', geschlecht='m')
        v.veranstalter.add(p0)
        v.veranstalter.add(p1)
        v.verantwortlich = p0

        # kein Semester angegeben
        response = self.client.post(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/generate_letters/'))

        # kein Abgabedatum angegeben
        response = self.client.post(self.path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/generate_letters/'))

        # keine zu evaluierenden Veranstaltungen
        ad = '10. - 11. November 2011'

        response = self.client.post(self.path,
                                    {'semester': s.semester, 'erhebungswoche': ad}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/generate_letters/'))

        # alles OK
        v.anzahl = 42
        v.sprache = 'en'
        v.save()

        self._delete_erhebungswoche_file()

        response = self.client.post(self.path,
                                    {'semester': s.semester, 'erhebungswoche': '10. - 11. November 2011',
                                     'vorlage': 'Anschreiben'}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 200)
        self.assertRegexpMatches(response['Content-Disposition'],
                                 r'^attachment; filename=[a-zA-Z0-9_-]+\.pdf$')
        self.assertEqual(ad, self._get_erhebungswoche())
        with open(settings.LATEX_PATH + 'veranstalter.adr', 'r') as f:
            self.assertEqual(f.readline().strip(),
                             '\\adrentry{Je Mand}{S202 D120}{Stoning I}{42}{en}{Vorlesung}{2000000001005}{}{}')

            # test Aufkleber
        response = self.client.post(self.path,
                                    {'semester': s.semester, 'erhebungswoche': '10. - 11. November 2011',
                                     'vorlage': 'Aufkleber'}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 200)
        self.assertRegexpMatches(response['Content-Disposition'],
                                 r'^attachment; filename=[a-zA-Z0-9_-]+\.pdf$')
        self.assertEqual(ad, self._get_erhebungswoche())
        with open(settings.LATEX_PATH + '../aufkleber/' + 'veranstalter.adr', 'r') as f:
            self.assertEqual(f.readline().strip(),
                             '\\adrentry{Je Mand}{S202 D120}{Stoning I}{42}{en}{Vorlesung}{2000000001005}{}{}')

        with self.settings(TEST_LATEX_ERROR=True):
            response = self.client.post(self.path,
                                        {'semester': s.semester, 'erhebungswoche': '10. - 11. November 2011',
                                         'vorlage': 'Anschreiben'}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/generate_letters.html')

        # test Aufkleber fuer grosse Veranstaltungen
        response = self.client.post(self.path,
                                    {'semester': s.semester, 'erhebungswoche': '10. - 11. November 2011',
                                     'vorlage': 'Grossaufkleber'}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        v.anzahl = 86
        v.save()
        response = self.client.post(self.path,
                                    {'semester': s.semester, 'erhebungswoche': '10. - 11. November 2011',
                                     'vorlage': 'Grossaufkleber'}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 200)
        self.assertRegexpMatches(response['Content-Disposition'],
                                 r'^attachment; filename=[a-zA-Z0-9_-]+\.pdf$')
        self.assertEqual(ad, self._get_erhebungswoche())
        with open(settings.LATEX_PATH + '../aufkleber/' + 'veranstalter.adr', 'r') as f:
            self.assertEqual(f.readline().strip(),
                             '\\adrentry{Je Mand}{S202 D120}{Stoning I}{86}{en}{Vorlesung}{2000000001005}{}{}')

        with self.settings(TEST_LATEX_ERROR=True):
            response = self.client.post(self.path,
                                        {'semester': s.semester, 'erhebungswoche': '10. - 11. November 2011',
                                         'vorlage': 'Anschreiben'}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/generate_letters.html')
