from io import StringIO

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse

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
    def checkXMLEqual(self, xml1, xml2):
        xml1 = xml1.replace("\n", "").replace("\t", "").replace(" ", "")
        xml2 = xml2.replace("\n", "").replace("\t", "").replace(" ", "")
        self.assertEqual(xml1, xml2)

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
        self.assertRegex(response['Content-Disposition'], r'^attachment; filename="[a-zA-Z0-9_-]+\.xml"$')
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
                        <EvaSys xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://evaluation.tu-darmstadt.de/evasys/doc/xml-import.xsd">
                            <Lecture key="lv-1">
                                <dozs></dozs>
                                <name>Stoning I</name>
                                <orgroot>FB 20</orgroot>
                                <short>123v-SS11</short>
                                <period>SS11</period>
                                <type>Vorlesung</type>
                                <turnout>42</turnout>
                                <p_o_study>Informatik</p_o_study>
                                <survey><EvaSysRef type="Survey" key="su-1" /></survey>
                                <external_id>lv-1</external_id>
                            </Lecture>
                            <Survey key="su-1">
                                <survey_form>FB20Vv1e</survey_form>
                                <survey_period>SS11</survey_period>
                                <survey_type>coversheet</survey_type>
                                <survey_verify>0</survey_verify>
                            </Survey>
                            <Lecture key="lv-2">
                                <dozs></dozs>
                                <name>Stoning I</name>
                                <orgroot>FB 20</orgroot>
                                <short>123vu-SS11</short>
                                <period>SS11</period>
                                <type>Vorlesung + Übung</type>
                                <turnout>23</turnout>
                                <p_o_study>Informatik</p_o_study>
                                <survey><EvaSysRef type="Survey" key="su-2" /></survey>
                                <external_id>lv-2</external_id>
                            </Lecture>
                            <Survey key="su-2">
                                <survey_form>FB20Vv1</survey_form>
                                <survey_period>SS11</survey_period>
                                <survey_type>coversheet</survey_type>
                                <survey_verify>0</survey_verify>
                            </Survey>
                        </EvaSys>'''
        self.checkXMLEqual(test_xml, response.content.decode('utf-8'))

        response = self.client.post(path, {'semester': s.semester, 'xml_ubung': True}, **{'REMOTE_USER': 'super'})
        self.assertRegex(response['Content-Disposition'], r'^attachment; filename="[a-zA-Z0-9_-]+\.xml"$')
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
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
                        <survey_form>FB20Üv1</survey_form>
                        <survey_period>SS11</survey_period>
                        <survey_type>coversheet</survey_type>
                        <survey_verify>0</survey_verify>
                        </Survey>
                        </EvaSys>
                        '''
        self.checkXMLEqual(test_xml, response.content.decode('utf-8'))

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
        self.assertRegex(response['Content-Disposition'], r'^attachment; filename="[a-zA-Z0-9_-]+\.xml"$')
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>\n
        <EvaSys xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n\t
        xsi:noNamespaceSchemaLocation="http://evaluation.tu-darmstadt.de/evasys/doc/xml-import.xsd">\n\t
        <Lecture key="lv-1">\n\t\t<dozs>\n\t\t\t\n\t\t\t<doz>\n\t\t\t\t<EvaSysRef type="Person" key="pe-2" />\n\t\t\t
        </doz>\n\t\t\t\n\t\t\t<doz>\n\t\t\t\t<EvaSysRef type="Person" key="pe-1" />\n\t\t\t</doz>\n\t\t\t\n\t\t\t<doz>
        \n\t\t\t\t<EvaSysRef type="Person" key="pe-3" />\n\t\t\t</doz>\n\t\t\t\n\t\t</dozs>\n\t\t<name>Stoning I</name>
        \n\t\t<orgroot>FB 20</orgroot>\n\t\t<short>123v-SS11</short>\n\t\t<period>SS11</period>\n\t\t
        <type>Vorlesung</type>\n\t\t<turnout>42</turnout>\n\t\t<p_o_study>Informatik</p_o_study>\n\t\t
        <survey>\n\t\t\t\n\t\t\t<EvaSysRef type="Survey" key="su-1" />\n\t\t\t\n\t\t</survey>\n\t\t
        <external_id>lv-1</external_id>\n\t</Lecture>\n\n\t\n\t<Survey key="su-1">\n\t\t
        <survey_form>FB20Vv1e</survey_form>\n\t\t<survey_period>SS11</survey_period>\n\t\t
        <survey_type>coversheet</survey_type>\n\t\t<survey_verify>0</survey_verify>\n\t</Survey>\n\t\n\t\n\t
        <Person key="pe-1">\n\t\t<firstname>Je</firstname>\n\t\t<lastname>Mand</lastname>\n\t\t
        <email>je@ma.nd</email>\n\t\t<gender>f</gender>\n\t\t<external_id>pe-1</external_id>\n\t
        </Person><Person key="pe-2">\n\t\t<firstname>Prim</firstname>\n\t\t<lastname>Ardozent</lastname>\n\t\t
        <email>prim@ardoz.ent</email>\n\t\t<gender>m</gender>\n\t\t<external_id>pe-2</external_id>\n\t</Person>
        <Person key="pe-3">\n\t\t<firstname>Je1</firstname>\n\t\t<lastname>Mand1</lastname>\n\t\t
        <email>je1@ma.nd</email>\n\t\t<gender>m</gender>\n\t\t<external_id>pe-3</external_id>\n\t</Person>\n
        </EvaSys>\n'''

        self.checkXMLEqual(test_xml, response.content.decode('utf-8'))


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

        # Vorschau: Check if the replacements are highlighted
        color_span = '<span style="color:blue">{}</span>'
        self.assertEqual(color_span.format('Grundlagen der Agrarphilosophie I') , response.context['veranstaltung'])
        link_veranstalter = 'https://www.fachschaft.informatik.tu-darmstadt.de%s' % reverse('veranstalter-login')
        link_suffix_format = '?vid=%d&token=%s'
        self.assertEqual(color_span.format(link_veranstalter + (link_suffix_format % (1337, '0123456789abcdef'))) , response.context['link_veranstalter'])

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