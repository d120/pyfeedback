# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test.client import Client

from feedback.models import Veranstaltung, Semester
from feedback import tests
from django.utils.translation import get_language

class NonSuTestMixin(TransactionTestCase):
    def setUp(self):
        super(NonSuTestMixin, self).setUp()
        self.u = User.objects.create_user(settings.USERNAME_VERANSTALTER, password='pw')
        self.su = User.objects.create_superuser('super', None, None)
        User.objects.create_superuser('supers', None, 'pw')

    def do_non_su_test(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].split('?')[0], tests.LOGIN_URL)

        self.assertTrue(self.client.login(username=settings.USERNAME_VERANSTALTER, password='pw'),
                        'Der Login mit dem Veranstalter-Account ist fehlgeschlagen. Wurde ' +
                        'moeglicherweise beim Ueberschreiben von setUp() der super()-Aufruf ' +
                        'vergessen?')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].split('?')[0], tests.LOGIN_URL)

        self.client.logout()


def get_veranstaltung(typ):
    s = Semester.objects.get_or_create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')[0]
    default_params = {'semester': s, 'status': Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET, 'grundstudium': False,
                      'evaluieren': True, 'lv_nr': '123' + typ}
    v = Veranstaltung.objects.create(typ=typ, name='Stoning I', **default_params)
    return s, v


def login_veranstalter(v):
    c = Client()
    response = c.get(f'/{get_language()}/feedback/veranstalter/login/', {'vid': v.id, 'token': v.access_token})
    if response.status_code != 302:
        raise Exception('Veranstalter-Login fehlgeschlagen.')
    return c
