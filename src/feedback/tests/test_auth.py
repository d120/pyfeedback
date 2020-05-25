# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from feedback.auth import VeranstalterBackend, TakeoverBackend, FSAccountBackend
from feedback.models import Person
from feedback.tests.tools import get_veranstaltung


class VeranstalterBackendTest(TestCase):
    def setUp(self):
        self.b = VeranstalterBackend()
        self.u = User.objects.create_user(username=settings.USERNAME_VERANSTALTER)
        self.p = Person.objects.create(vorname='Brian', nachname='Cohen')
        self.s, self.v = get_veranstaltung('v')
        self.v.access_token = '0123456789abcdef'
        self.v.veranstalter.add(self.p)
        self.v.save()
    
    def test_authenticate(self):
        vid = self.v.id
        self.assertFalse(self.b.authenticate(request=None, vid=vid, token=None))
        self.assertFalse(self.b.authenticate(request=None, vid=None, token='0123456789abcdef'))
        self.assertFalse(self.b.authenticate(request=None, vid=vid, token='000'))
        self.assertEqual(self.b.authenticate(request=None, vid=vid, token='0123456789abcdef'), self.u)
        self.u.delete()
        self.assertFalse(self.b.authenticate(request=None, vid=vid, token='0123456789abcdef'))


class TakeoverBackendTest(TestCase):
    def setUp(self):
        self.b = TakeoverBackend()
        self.ub = User.objects.create_user(username='brian')
        self.uj = User.objects.create_user(username='judith')
        self.uj.is_superuser = True
    
    def test_authenticate(self):
        self.assertFalse(self.b.authenticate(request=None, user=self.ub))
        self.assertFalse(self.b.authenticate(request=None, user=self.ub, current_user=self.ub))
        self.assertEqual(self.b.authenticate(request=None, user=self.ub, current_user=self.uj), self.ub)
        self.assertEqual(self.b.authenticate(request=None, user=self.ub, reset=True), self.ub)


class FSAccountBackendTest(TestCase):
    def setUp(self):
        self.b = FSAccountBackend()
        self.u = User.objects.create_user('brian')
    
    def test_configure_user(self):
        self.assertTrue(self.b.configure_user(self.u).is_superuser)
        u_db = User.objects.get(username='brian')
        self.assertTrue(u_db.is_superuser)
