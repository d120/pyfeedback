# coding=utf-8

from base64 import b64encode

from django.test import TestCase
from django.test.utils import override_settings

from feedback.tests.tools import NonSuTestMixin, get_veranstaltung
from feedback import tests
from feedback.models import Veranstaltung


class InternAuthTest(NonSuTestMixin, TestCase):
    def setUp(self):
        super(InternAuthTest, self).setUp()
        _, self.v = get_veranstaltung('vu')

    def test_login_logged_in(self):
        self.client.login(username='supers', password='pw')
        response = self.client.get(tests.LOGIN_URL, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], tests.INDEX_URL)

    @override_settings(DEBUG=True)
    def test_login_debug_auth(self):
        response = self.client.get(tests.LOGIN_URL)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response['WWW-Authenticate'], 'Basic realm="Feedback"')

        extra = {'HTTP_AUTHORIZATION': 'Basic ' + b64encode('super:secretpw')}
        response = self.client.get(tests.LOGIN_URL, **extra)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], tests.INDEX_URL)

    def test_rechte_uebernehmen(self):
        path = '/intern/rechte_uebernehmen/'
        self.do_non_su_test(path)

        self.assertTrue(self.client.login(username='supers', password='pw'))
        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'intern/rechte_uebernehmen.html')
        self.assertSequenceEqual(response.context['veranstaltungen'], [self.v])

        response = self.client.post(path, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.templates[0].name, 'intern/rechte_uebernehmen.html')

        response = self.client.post(path, {'vid': self.v.id}, **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/veranstalter/'))

    def test_rechte_zuruecknehmen(self):
        self.client.login(username='supers', password='pw')
        self.client.post('/intern/rechte_uebernehmen/', {'vid': self.v.id}, **{'REMOTE_USER': 'super'})

        response = self.client.get('/intern/rechte_zuruecknehmen/', **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], tests.INDEX_URL)

    def test_rechte_zuruecknehmen_no_origin_uid(self):
        """Es sollen rechte wiederhergestellt werden die vorher nicht abgegebn wurden"""
        self.assertTrue(self.client.login(username='supers', password='pw'))
        response = self.client.get('/intern/rechte_zuruecknehmen/', **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].split('?')[0].endswith(tests.INDEX_END))
