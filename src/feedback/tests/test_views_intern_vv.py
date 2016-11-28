# coding=utf-8

from StringIO import StringIO

from django.conf import settings
from django.test import TestCase

from feedback.forms import UploadFileForm
from feedback.models import Semester, ImportCategory, ImportVeranstaltung, ImportPerson, Person
from feedback.tests.tools import NonSuTestMixin, get_veranstaltung

from feedback import tests


class InternVvTest(NonSuTestMixin):
    def test_import_vv(self):
        path = '/intern/import_vv/'
        self.do_non_su_test(path)

        self.assertTrue(self.client.login(username='supers', password='pw'))
        response = self.client.get(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_vv.html')
        self.assertTrue(isinstance(response.context['form'], UploadFileForm))

        response = self.client.post(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_vv.html')
        self.assertTrue(isinstance(response.context['form'], UploadFileForm))

        #        f = StringIO('blablabla')
        #        f.name = 'test.csv'
        #        response = self.client.post(self.path, {'file': f})
        #        f.close()

        with open(settings.TESTDATA_PATH + 'vv_test.xml', 'r') as f:
            response = self.client.post(path, {'file': f}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/import_vv_edit/'))

    def test_import_vv_edit_get(self):
        path = '/intern/import_vv_edit/'
        self.do_non_su_test(path)

        self.client.login(username='supers', password='pw')
        response = self.client.get(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/import_vv/'))

        ic = ImportCategory.objects.create(parent=None, name='root', rel_level=1)
        response = self.client.get(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_vv_edit.html')
        self.assertSequenceEqual(response.context['semester'], list(Semester.objects.all()))
        self.assertEqual(response.context['vv'], [])

    def test_import_vv_edit_post(self):
        s = Semester.objects.create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')
        ic = ImportCategory.objects.create(parent=None, name='root', rel_level=1)
        ic_sub = ImportCategory.objects.create(parent=ic, name='sub', rel_level=1)
        ip = ImportPerson.objects.create(vorname='Das', nachname='Wesen')
        iv0 = ImportVeranstaltung.objects.create(typ='vu', name='Bla I', category=ic)
        iv0.veranstalter.add(ip)
        iv1 = ImportVeranstaltung.objects.create(typ='vu', name='Bla II', category=ic)
        iv1_sub = ImportVeranstaltung.objects.create(typ='vu', name='Bla II', category=ic_sub)

        self.client.login(username='supers', password='pw')
        path = '/intern/import_vv_edit/'

        # kein Semester angegeben
        response = self.client.post(path, {'v': [iv0.id, iv1.id, iv1_sub.id]}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/import_vv_edit/'))

        # keine Vorlesungen angegeben
        response = self.client.post(path, {'semester': s.semester}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/import_vv_edit/'))

        # beides angegeben
        response = self.client.post(path, {'v': [iv0.id, iv1.id, iv1_sub.id], 'semester': s.semester},
                                    **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/intern/import_vv_edit_users/'))


class InternVvEditUsersTest(NonSuTestMixin, TestCase):
    def setUp(self):
        super(InternVvEditUsersTest, self).setUp()
        self.path = '/intern/import_vv_edit_users/'

        self.p0 = Person.objects.create(vorname='Je', nachname='Mand')
        self.p1 = Person.objects.create(vorname='Auch Je', nachname='Mand')
        self.p2 = Person.objects.create(vorname="Noch Je", nachname='Mand')

        self.path_save_p0 = self.path + str(self.p0.id) + '/'
        self.path_save_p1 = self.path + str(self.p1.id) + '/'
        self.path_save_p2 = self.path + str(self.p2.id) + '/namecheck/'

        _, self.v = get_veranstaltung('vu')
        self.v.veranstalter.add(self.p0)
        self.v.veranstalter.add(self.p1)

    def test_import_vv_edit_users_get(self):
        self.do_non_su_test(self.path)

        self.assertTrue(self.client.login(username='supers', password='pw'))
        response = self.client.get(self.path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_vv_edit_users.html')

    def test_import_vv_edit_users_post(self):
        self.do_non_su_test(self.path_save_p0)

        self.client.login(username='supers', password='pw')

        response = self.client.get(self.path_save_p0)
        self.assertEqual(response.templates[0].name, 'intern/import_vv_edit_users_update.html')

        response = self.client.get(self.path_save_p1)
        self.assertEqual(response.templates[0].name, 'intern/import_vv_edit_users_update.html')

        response = self.client.post(self.path_save_p0, {'geschlecht': 'm', 'email': ''})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(self.path_save_p0, {'geschlecht': 'm', 'email': 'ad@res.se'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'], tests.LOGIN_URL)

        response = self.client.post(self.path_save_p1, {'geschlecht': 'm', 'email': 'ad2@res.se'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'], tests.LOGIN_URL)

    def test_import_vv_edit_users_namecheck_get(self):
        self.do_non_su_test(self.path_save_p2)
        self.assertTrue(self.client.login(username='supers', password='pw'))

        response = self.client.get(self.path_save_p2, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/import_vv_edit_users_namecheck.html')

    def test_import_vv_edit_users_namecheck_post(self):
        self.do_non_su_test(self.path_save_p2)
        self.client.login(username='supers', password='pw')

        response = self.client.get(self.path_save_p2)
        self.assertEqual(response.templates[0].name, 'intern/import_vv_edit_users_namecheck.html')

        response = self.client.post(self.path_save_p2, {'id_new': str(self.p1.id), 'id_old': str(self.p2.id),
                                                        'similar': 'Zusammenführen'})
        self.assertEqual(response.status_code, 302)