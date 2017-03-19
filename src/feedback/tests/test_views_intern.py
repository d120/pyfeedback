# coding=utf-8

import os

from StringIO import StringIO

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse

from feedback.forms import UploadFileForm
from feedback.models import Semester, Person, Veranstaltung, Fragebogen2009, Mailvorlage, Einstellung, \
    Fachgebiet, FachgebietEmail
from feedback.tests.tools import NonSuTestMixin, get_veranstaltung

from feedback import tests


class CloseOrderTest(NonSuTestMixin, TestCase):
    def setUp(self):
        self.client.login(username='supers', password='pw')
        self.s, self.v = get_veranstaltung('vu')

    def test_close_order_bestellung_liegt_vor_post(self):
        path = '/intern/status_final/'
        self.v.status = Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR
        self.v.save()

        response = self.client.post(path, {'auswahl': 'ja', 'submit': 'Bestätigen'}, **{'REMOTE_USER': 'super'})

        self.v.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_BESTELLUNG_WIRD_VERARBEITET)

    def test_close_order_keine_evaluation_post(self):
        path = '/intern/status_final/'
        self.v.status = Veranstaltung.STATUS_KEINE_EVALUATION
        self.v.save()

        response = self.client.post(path, {'auswahl': 'ja', 'submit': 'Bestätigen'}, **{'REMOTE_USER': 'super'})

        self.v.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION_FINAL)

    def test_close_order_status_angelegt_post(self):
        path = '/intern/status_final/'
        self.v.status = Veranstaltung.STATUS_ANGELEGT
        self.v.save()

        response = self.client.post(path, {'auswahl': 'ja', 'submit': 'Bestätigen'}, **{'REMOTE_USER': 'super'})

        self.v.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION_FINAL)

    def test_close_order_bestellung_geoeffnet_post(self):
        path = '/intern/status_final/'
        self.v.status = Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET
        self.v.save()

        response = self.client.post(path, {'auswahl': 'ja', 'submit': 'Bestätigen'}, **{'REMOTE_USER': 'super'})

        self.v.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION_FINAL)

    def test_close_order_refuse(self):
        path = '/intern/status_final/'
        self.v.status = Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR
        self.v.save()

        response = self.client.post(path, {'auswahl': 'nein', 'submit': 'Bestätigen'}, **{'REMOTE_USER': 'super'})

        self.v.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR)


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
        empty_semester = Semester.objects.create(semester=20120, fragebogen='2009', sichtbarkeit='ADM')

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

        response = self.client.post(path, {'semester': empty_semester.semester, 'xml_ubung': True}, **{'REMOTE_USER': 'super'})
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

        self.assertXMLEqual(response.content,
                         '''<?xml version="1.0" encoding="UTF-8"?>
<EvaSys xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:noNamespaceSchemaLocation="http://evaluation.tu-darmstadt.de/evasys/doc/xml-import.xsd">
<Lecture key="lv-1">
<dozs>

</dozs>
<name>Stoning I</name>
<orgroot>FB 20</orgroot>
<short>123v-SS11</short>
<period>SS11</period>
<type>Vorlesung</type>
<turnout>42</turnout>
<p_o_study>Informatik</p_o_study>
<survey>
<EvaSysRef type="Survey" key="su-1" />
</survey>
<external_id>lv-1</external_id>
</Lecture>
<Survey key="su-1">
<survey_form>FB20Vv1e</survey_form>
<survey_period>SS11</survey_period>
<survey_type>coversheet</survey_type>
<survey_verify>0</survey_verify>
</Survey>
<Lecture key="lv-2">
<dozs>

</dozs>
<name>Stoning I</name>
<orgroot>FB 20</orgroot>
<short>123vu-SS11</short>
<period>SS11</period>
<type>Vorlesung + Übung</type>
<turnout>23</turnout>
<p_o_study>Informatik</p_o_study>
<survey>
<EvaSysRef type="Survey" key="su-2" />
</survey>
<external_id>lv-2</external_id>
</Lecture>
<Survey key="su-2">
<survey_form>FB20Vv1</survey_form>
<survey_period>SS11</survey_period>
<survey_type>coversheet</survey_type>
<survey_verify>0</survey_verify>
</Survey>
</EvaSys>
''')
        response = self.client.post(path, {'semester': s.semester, 'xml_ubung': True}, **{'REMOTE_USER': 'super'})
        self.assertRegexpMatches(response['Content-Disposition'],
                                 r'^attachment; filename="[a-zA-Z0-9_-]+\.xml"$')

        self.assertXMLEqual(response.content, '''<?xml version="1.0" encoding="UTF-8"?>
<EvaSys xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:noNamespaceSchemaLocation="http://evaluation.tu-darmstadt.de/evasys/doc/xml-import.xsd">
<Lecture key="lv-2">
<dozs>

</dozs>
<name>Stoning I</name>
<orgroot>FB 20</orgroot>
<short>123vu-SS11</short>
<period>SS11</period>
<type>Vorlesung + Übung</type>
<turnout>23</turnout>
<p_o_study>Informatik</p_o_study>
<survey>
<EvaSysRef type="Survey" key="su-2-u" />
</survey>
<external_id>lv-2</external_id>
</Lecture>
<Survey key="su-2-u">
<survey_form>FB20\xc3\x9cv1</survey_form>
<survey_period>SS11</survey_period>
<survey_type>coversheet</survey_type>
<survey_verify>0</survey_verify>
</Survey>
</EvaSys>
''')

    def test_export_veranstaltungen_post_primaerdozent(self):
        path = '/intern/export_veranstaltungen/'
        self.client.login(username='supers', password='pw')

        s, v = get_veranstaltung('v')
        p1 = Person.objects.create(vorname='Je', nachname='Mand', email='je@ma.nd', geschlecht='w')
        p2 = Person.objects.create(vorname='Prim', nachname='Ardozent', email='prim@ardoz.ent', geschlecht='m')
        p3 = Person.objects.create(vorname='Je1', nachname='Mand1', email='je1@ma.nd', geschlecht='m')

        v.veranstalter.add(p1)
        v.veranstalter.add(p2)
        v.veranstalter.add(p3)
        v.ergebnis_empfaenger.add(p1)
        v.ergebnis_empfaenger.add(p2)
        v.ergebnis_empfaenger.add(p3)

        v.grundstudium = True
        v.sprache = 'en'
        v.verantwortlich = p1
        v.primaerdozent = p2
        v.anzahl = 42
        v.save()

        response = self.client.post(path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertRegexpMatches(response['Content-Disposition'],
                                 r'^attachment; filename="[a-zA-Z0-9_-]+\.xml"$')

        self.assertXMLEqual(response.content,
                             '''<?xml version="1.0" encoding="UTF-8"?>
<EvaSys xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:noNamespaceSchemaLocation="http://evaluation.tu-darmstadt.de/evasys/doc/xml-import.xsd">
<Lecture key="lv-1">
<dozs>
<doz>
<EvaSysRef type="Person" key="pe-2" />
</doz>
<doz>
<EvaSysRef type="Person" key="pe-1" />
</doz>
<doz>
<EvaSysRef type="Person" key="pe-3" />
</doz>
</dozs>
<name>Stoning I</name>
<orgroot>FB 20</orgroot>
<short>123v-SS11</short>
<period>SS11</period>
<type>Vorlesung</type>
<turnout>42</turnout>
<p_o_study>Informatik</p_o_study>
<survey>
<EvaSysRef type="Survey" key="su-1" />
</survey>
<external_id>lv-1</external_id>
</Lecture>
<Survey key="su-1">
<survey_form>FB20Vv1e</survey_form>
<survey_period>SS11</survey_period>
<survey_type>coversheet</survey_type>
<survey_verify>0</survey_verify>
</Survey>
<Person key="pe-1">
<firstname>Je</firstname>
<lastname>Mand</lastname>
<email>je@ma.nd</email>
<gender>f</gender>
<external_id>pe-1</external_id>
</Person><Person key="pe-2">
<firstname>Prim</firstname>
<lastname>Ardozent</lastname>
<email>prim@ardoz.ent</email>
<gender>m</gender>
<external_id>pe-2</external_id>
</Person><Person key="pe-3">
<firstname>Je1</firstname>
<lastname>Mand1</lastname>
<email>je1@ma.nd</email>
<gender>m</gender>
<external_id>pe-3</external_id>
</Person>
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

        fb = Fachgebiet.objects.create(name="Fachgebiet1", kuerzel="FB1")
        FachgebietEmail.objects.create(fachgebiet=fb, email_suffix="ul.bla", email_sekretaerin="sek@ul.bla")
        p1 = Person.objects.create(vorname='Pe', nachname='Ter', email='pe@ter.bla')
        p2 = Person.objects.create(vorname='Pa', nachname='Ul', email='pa@ul.bla', fachgebiet=fb)

        v1.veranstalter.add(p1)
        v1.veranstalter.add(p2)
        mv = Mailvorlage.objects.create(subject='Testmail', body='Dies ist eine Testmail.')
        Einstellung.objects.create(name='bestellung_erlaubt', wert='0')

        data = {
            'uebernehmen': 'x',
            'recipient': [Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET],
            'subject': 'abc',
            'body': 'xyz'
        }

        # kein Semester angegeben
        response = self.client.post(self.path, data, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sendmail/'))

        # Vorlage übernehmen; Vorlage nicht angegeben
        data['semester'] = s.semester
        response = self.client.post(self.path, data, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/sendmail/'))

        # Vorlage übernehmen; Vorlage ist angegeben
        data['vorlage'] = mv.id
        response = self.client.post(self.path, data, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/sendmail.html')
        self.assertEqual(response.context['subject'], mv.subject)
        self.assertEqual(response.context['body'], mv.body)

        # Vorschau; Empfänger ist auf Veranstalter mit fehlenden Bestellungen eingestellt
        del data['uebernehmen']
        data['vorschau'] = 'x'
        response = self.client.post(self.path, data, **{'REMOTE_USER': 'super'})
        self.assertIn('intern/sendmail_preview.html', (t.name for t in response.templates))
        self.assertTrue(response.context['vorschau'])

        # Vorschau; Empfänger ist auf Veranstaltungen mit Ergebnissen eingestellt
        data['recipient'] = [Veranstaltung.STATUS_ERGEBNISSE_VERSANDT]
        response = self.client.post(self.path, data, **{'REMOTE_USER': 'super'})
        self.assertIn('intern/sendmail_preview.html', (t.name for t in response.templates))
        self.assertTrue(response.context['vorschau'])

        # Vorschau: Check if the replacements are highlighted
        color_span = '<span style="color:blue">{}</span>'
        self.assertEqual(color_span.format('Grundlagen der Agrarphilosophie I') , response.context['veranstaltung'])
        link_veranstalter = 'https://www.fachschaft.informatik.tu-darmstadt.de%s' % reverse('veranstalter-login')
        link_suffix_format = '?vid=%d&token=%s'
        self.assertEqual(color_span.format(link_veranstalter + (link_suffix_format % (1337, '0123456789abcdef'))),
                         response.context['link_veranstalter'])

        # Senden
        del data['vorschau']
        data['senden'] = 'x'
        data['recipient'] = [0]  # 0 ist hierbei der Code für alle Veranstaltungen
        del data['vorlage']
        response = self.client.post(self.path, data, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'], tests.LOGIN_URL)
        # Hier wird in Eclipse ein Fehler angezeigt; mail.outbox gibt es während der Testläufe
        # aber wirklich (siehe https://docs.djangoproject.com/en/1.4/topics/testing/#email-services)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(len(mail.outbox[0].to), 3)  # an zwei veranstalter und sekretaerin
