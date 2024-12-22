# coding=utf-8

from base64 import b64encode

from django.test import TestCase
from django.test.utils import override_settings

from feedback.tests.tools import NonSuTestMixin, get_veranstaltung
from feedback import tests
from feedback.models import Veranstaltung
from django.utils.translation import get_language
from django.contrib.auth.models import User
from django.urls import reverse

class InternAuthTest(NonSuTestMixin, TestCase):
    def setUp(self):
        super(InternAuthTest, self).setUp()
        _, self.v = get_veranstaltung('vu')
        self.username = 'supers1'
        self.password = 'pw1'
        self.user = User.objects.create_user(username=self.username, password=self.password)

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

        extra = {'HTTP_AUTHORIZATION': 'Basic ' + str(b64encode(b'super:secretpw'))}
        response = self.client.get(tests.LOGIN_URL, **extra)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], tests.INDEX_URL)

    def test_auth_user(self) :
        response = self.client.get(tests.AUTH_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_auth_user_post_valid(self) :
        response = self.client.post(tests.AUTH_URL, {'username':self.username, 'password':self.password})
        self.assertRedirects(response, tests.LOGIN_URL, target_status_code=302)

        login_required_url = reverse('feedback:intern-index')

        response = self.client.get(login_required_url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(response['Location'].split('?')[0].endswith(tests.LOGIN_URL))
        self.assertTrue(response['Location'].split('?')[1].endswith(login_required_url))

    def test_auth_post_invalid_credentials(self) :
        response = self.client.post(tests.AUTH_URL,{'username': self.username,'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertContains(response, "Invalid Password or Username")

    def test_auth_user_post_missing_data(self):
        response = self.client.post(tests.AUTH_URL, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertContains(response, "Invalid Password or Username")

    def test_rechte_uebernehmen(self):
        path = f'/{get_language()}/feedback/intern/rechte_uebernehmen/'
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
        self.client.post(f'/{get_language()}/feedback/intern/rechte_uebernehmen/', {'vid': self.v.id}, **{'REMOTE_USER': 'super'})

        response = self.client.get(f'/{get_language()}/feedback/intern/rechte_zuruecknehmen/', **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], tests.INDEX_URL)

    def test_rechte_zuruecknehmen_no_origin_uid(self):
        """Es sollen rechte wiederhergestellt werden die vorher nicht abgegebn wurden"""
        self.assertTrue(self.client.login(username='supers', password='pw'))
        response = self.client.get(f'/{get_language()}/feedback/intern/rechte_zuruecknehmen/', **{'REMOTE_USER': 'super'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].split('?')[0].endswith(tests.INDEX_END))
