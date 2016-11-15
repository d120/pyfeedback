# coding=utf-8

import os

from StringIO import StringIO

from django.conf import settings
from django.core import mail
from django.test import TestCase

from feedback.forms import UploadFileForm
from feedback.models import Semester, Person, Veranstaltung, Fragebogen2009, Mailvorlage, Einstellung
from feedback.tests.tools import NonSuTestMixin, get_veranstaltung

from feedback import tests


class InternMiscTest(NonSuTestMixin, TestCase):
    def test_index(self):
        path = tests.INDEX_END
        self.do_non_su_test(path)
        self.client.login(username='supers', password='pw')

        s = Semester.objects.create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')

        response = self.client.get(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/index.html')
        self.assertEqual(response.context['cur_semester'], s)

    def test_fragebogensprache(self):
        path = '/intern/fragebogensprache/'
        self.do_non_su_test(path)
        self.client.login(username='supers', password='pw')

        Semester.objects.create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')

        response = self.client.get(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/fragebogensprache.html')

    def test_export_veranstaltungen_get(self):
        path = '/intern/export_veranstaltungen/'
        self.do_non_su_test(path)
        self.client.login(username='supers', password='pw')

        response = self.client.get(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/export_veranstaltungen.html')
        self.assertSequenceEqual(response.context['semester'], list(Semester.objects.all()))


class ExportVeranstaltungenTest(NonSuTestMixin, TestCase):
    def test_export_veranstaltungen_post(self):
        path = '/intern/export_veranstaltungen/'
        self.client.login(username='supers', password='pw')
        self.client.login(username='supers', password='pw')

        _, v1 = get_veranstaltung('v')
        s, v2 = get_veranstaltung('vu')
        p = Person.objects.create(vorname='Je', nachname='Mand', email='je@ma.nd', geschlecht='w')
        v1.veranstalter.add(p)
        v2.veranstalter.add(p)

        v1.grundstudium = True
        v1.sprache = 'en'
        v1.verantwortlich = p
        v1.save()

        # kein Semester angegeben
        response = self.client.post(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/export_veranstaltungen/'))

        # keine Bestellung vorhanden
        response = self.client.post(path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/export_veranstaltungen/'))

        # niemand als Verantwortlicher eingetragen
        v1.anzahl = 42
        v1.save()
        v2.anzahl = 23
        v2.save()
        response = self.client.post(path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/export_veranstaltungen/'))

        # keine Sprache angegeben
        v2.verantwortlich = p
        v2.save()
        response = self.client.post(path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/export_veranstaltungen/'))

        # alles OK
        v2.sprache = 'de'
        v2.save()
        response = self.client.post(path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertRegexpMatches(response['Content-Disposition'],
                                 r'^attachment; filename="[a-zA-Z0-9_-]+\.xml"$')

        # TODO: Use SimpleTestCase.assertXMLEqual when Django is on newer version
        self.assertEqual(response.content,
                         '''<?xml version="1.0" encoding="UTF-8"?>
<EvaSys xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
\txsi:noNamespaceSchemaLocation="http://evaluation.tu-darmstadt.de/evasys/doc/xml-import.xsd">
\t<Lecture key="lv-1">
\t\t<dozs>
\t\t\t
\t\t</dozs>
\t\t<name>Stoning I</name>
\t\t<orgroot>FB 20</orgroot>
\t\t<short>123v-SS11</short>
\t\t<period>SS11</period>
\t\t<type>Vorlesung</type>
\t\t<turnout>42</turnout>
\t\t<p_o_study>Informatik</p_o_study>
\t\t<survey>
\t\t\t<EvaSysRef type="Survey" key="su-1" />
\t\t\t
\t\t</survey>
\t\t<external_id>lv-1</external_id>
\t</Lecture>
\t<Survey key="su-1">
\t\t<survey_form>FB20Vv1e</survey_form>
\t\t<survey_period>SS11</survey_period>
\t\t<survey_type>coversheet</survey_type>
\t\t<survey_verify>0</survey_verify>
\t</Survey>
\t
\t<Lecture key="lv-2">
\t\t<dozs>
\t\t\t
\t\t</dozs>
\t\t<name>Stoning I</name>
\t\t<orgroot>FB 20</orgroot>
\t\t<short>123vu-SS11</short>
\t\t<period>SS11</period>
\t\t<type>Vorlesung + Übung</type>
\t\t<turnout>23</turnout>
\t\t<p_o_study>Informatik</p_o_study>
\t\t<survey>
\t\t\t<EvaSysRef type="Survey" key="su-2" />
\t\t\t<EvaSysRef type="Survey" key="su-2-u" />
\t\t</survey>
\t\t<external_id>lv-2</external_id>
\t</Lecture>
\t<Survey key="su-2">
\t\t<survey_form>FB20Vv1</survey_form>
\t\t<survey_period>SS11</survey_period>
\t\t<survey_type>coversheet</survey_type>
\t\t<survey_verify>0</survey_verify>
\t</Survey>
\t
\t<Survey key="su-2-u">
\t\t<survey_form>FB20Üv1</survey_form>
\t\t<survey_period>SS11</survey_period>
\t\t<survey_type>coversheet</survey_type>
\t\t<survey_verify>0</survey_verify>
\t</Survey>
\t
\t
\t
</EvaSys>
''')


#
class ImportErgebnisseTest(NonSuTestMixin, TestCase):
    def setUp(self):
        super(ImportErgebnisseTest, self).setUp()
        self.path = '/intern/import_ergebnisse/'
        self.s = Semester.objects.create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')

    def test_get(self):
        self.do_non_su_test(self.path)
        self.client.login(username='supers', password='pw')

        response = self.client.get(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_ergebnisse.html')
        self.assertSequenceEqual(response.context['semester'], [self.s])
        self.assertTrue(isinstance(response.context['form'], UploadFileForm))

    def test_post(self):
        self.client.login(username='supers', password='pw')
        default_params = {'semester': self.s, 'grundstudium': False, 'evaluieren': True}
        Veranstaltung.objects.create(name='Test I', lv_nr='1', **default_params)

        # kein Semester angegeben
        response = self.client.post(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/import_ergebnisse/'))

        # unvollständiges Formular
        response = self.client.post(self.path, {'semester': self.s.semester, 'file': ''}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_ergebnisse.html')

        # fehlerhafte Datei angegeben
        f = StringIO('b;l;a;b;l;a;b;l;a')
        f.name = 'test.csv'
        response = self.client.post(self.path, {'semester': self.s.semester, 'file': f}, **{'REMOTE_USER': 'super'})
        f.close()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sync_ergebnisse/'))

        # alles OK
        with open(settings.TESTDATA_PATH + 'ergebnis_test_20115.csv', 'r') as f:
            response = self.client.post(self.path, {'semester': self.s.semester, 'file': f}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sync_ergebnisse/'))


class SyncErgebnisseTest(NonSuTestMixin, TestCase):
    def setUp(self):
        super(SyncErgebnisseTest, self).setUp()
        self.path = '/intern/sync_ergebnisse/'
        self.s, self.v = get_veranstaltung('v')

    def test_get(self):
        self.do_non_su_test(self.path)
        self.client.login(username='supers', password='pw')

        response = self.client.get(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/sync_ergebnisse.html')
        self.assertSequenceEqual(response.context['semester'], [self.s])

    def test_post(self):
        self.client.login(username='supers', password='pw')

        # kein Semester angegeben
        response = self.client.post(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sync_ergebnisse/'))

        # keine Ergebnisse gefunden
        response = self.client.post(self.path, {'semester': self.s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sync_ergebnisse/'))

        # alles OK
        Fragebogen2009.objects.create(veranstaltung=self.v, ue_gesamt=1,
                                      ue_e=2, ue_f=3,
                                      ue_a=4, ue_b=5, ue_c=1, ue_d=2,
                                      ue_g=3, ue_i=4, ue_j=5, ue_k=1)
        response = self.client.post(self.path, {'semester': self.s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sync_ergebnisse/'))


class SendmailTest(NonSuTestMixin, TestCase):
    path = '/intern/sendmail/'

    def test_get(self):
        self.do_non_su_test(self.path)
        self.client.login(username='supers', password='pw')

        response = self.client.get(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/sendmail.html')

    def test_post(self):
        self.client.login(username='supers', password='pw')
        get_veranstaltung('v')
        s, v1 = get_veranstaltung('vu')
        v1.anzahl = 42
        v1.sprache = 'de'
        v1.save()
        v1.veranstalter.add(Person.objects.create(vorname='Pe', nachname='Ter', email='pe@ter.bla'))
        v1.veranstalter.add(Person.objects.create(vorname='Pa', nachname='Ul', email='pa@ul.bla'))
        mv = Mailvorlage.objects.create(subject='Testmail', body='Dies ist eine Testmail.')
        Einstellung.objects.create(name='bestellung_erlaubt', wert='0')

        params = {'uebernehmen': 'x', 'recipient': 'cur_sem_missing_order', 'subject': 'abc', 'body': 'xyz'}

        # kein Semester angegeben
        response = self.client.post(self.path, params, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sendmail/'))

        # Vorlage übernehmen; Vorlage nicht angegeben
        params['semester'] = s.semester
        response = self.client.post(self.path, params, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sendmail/'))

        # Vorlage übernehmen; Vorlage ist angegeben
        params['vorlage'] = mv.id
        response = self.client.post(self.path, params, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/sendmail.html')
        self.assertEqual(response.context['subject'], mv.subject)
        self.assertEqual(response.context['body'], mv.body)

        # Vorschau; Empfänger ist auf Veranstalter mit fehlenden Bestellungen eingestellt
        del params['uebernehmen']
        params['vorschau'] = 'x'
        response = self.client.post(self.path, params, **{'REMOTE_USER': 'super'})
        self.assertIn('intern/sendmail_preview.html', (t.name for t in response.templates))
        self.assertTrue(response.context['vorschau'])

        # Vorschau; Empfänger ist auf Veranstaltungen mit Ergebnissen eingestellt
        params['recipient'] = 'cur_sem_results'
        response = self.client.post(self.path, params, **{'REMOTE_USER': 'super'})
        self.assertIn('intern/sendmail_preview.html', (t.name for t in response.templates))
        self.assertTrue(response.context['vorschau'])

        # Senden
        del params['vorschau']
        params['senden'] = 'x'
        params['recipient'] = 'cur_sem_all'
        del params['vorlage']
        response = self.client.post(self.path, params, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'], tests.LOGIN_URL)
        # Hier wird in Eclipse ein Fehler angezeigt; mail.outbox gibt es während der Testläufe
        # aber wirklich (siehe https://docs.djangoproject.com/en/1.4/topics/testing/#email-services)
        self.assertEqual(len(mail.outbox), 2)
