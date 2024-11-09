import os
from subprocess import call

from django.test import TestCase, tag
from django.conf import settings

from feedback.models import Semester, Person, Veranstaltung, Fragebogen2009, Mailvorlage
from feedback.tests.tools import NonSuTestMixin, get_veranstaltung
from django.utils.translation import get_language

@tag('latex')
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

        self.path = f'/{get_language()}/intern/generate_letters/'
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
    
    ## test_post is deleted as latex no longer in use