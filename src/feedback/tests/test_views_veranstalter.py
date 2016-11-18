# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from feedback.forms import BestellungModelForm, KommentarModelForm
from feedback.models import Einstellung, Person, Veranstaltung
from feedback.tests.tools import get_veranstaltung, login_veranstalter


class VeranstalterLoginTest(TestCase):
    def setUp(self):
        _, self.v = get_veranstaltung('vu')
        User.objects.create_user(settings.USERNAME_VERANSTALTER)
    
    def test_incomplete_params(self):
        response = self.client.get('/veranstalter/login/')
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')
    
        response = self.client.get('/veranstalter/login/', {'vid': self.v.id})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')
        
        response = self.client.get('/veranstalter/login/', {'token': self.v.access_token})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')
    
    def test_bad_params(self):
        response = self.client.get('/veranstalter/login/', {'vid': self.v.id, 'token': 'inkorrekt'})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')
        
        response = self.client.get('/veranstalter/login/', {'vid': 123, 'token': self.v.access_token})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')
    
    def test_ok(self):
        response = self.client.get('/veranstalter/login/', {'vid': self.v.id,
                                                            'token': self.v.access_token})
        self.assertEqual(response.status_code, 302)


class VeranstalterIndexTest(TestCase):
    def setUp(self):
        User.objects.create_user(settings.USERNAME_VERANSTALTER)
        self.s, self.v = get_veranstaltung('vu')
        self.p = Person.objects.create()
        self.v.veranstalter.add(self.p)
    
    def test_unauth(self):
        response = self.client.get('/veranstalter/')
        self.assertEqual(response.templates[0].name, 'veranstalter/not_authenticated.html')
    
    def test_nothing(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='0')
        c = login_veranstalter(self.v)
        response = c.get('/veranstalter/')
        ctx = response.context
        self.assertEqual(ctx['veranstaltung'], self.v)
        with self.assertRaises(KeyError):
            ctx['order_form']
        with self.assertRaises(KeyError):
            ctx['comment_form']
    
    def test_get_bestellung(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response = c.get('/veranstalter/')
        ctx = response.context
        self.assertTrue(isinstance(ctx['order_form'], BestellungModelForm))
        self.assertNotContains(response,'Information zur Vollerhebung')
        self.assertContains(response,'Evaluieren:')
        
    def test_get_bestellung_vollerhebung(self):
        """Teste ob der Hinweis zur Vollerhebung angezeigt wird und ein Austragen
        nicht möglich ist"""
        self.s.vollerhebung = True
        self.s.save()
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response = c.get('/veranstalter/')
        ctx = response.context
        self.assertTrue(isinstance(ctx['order_form'], BestellungModelForm))
        self.assertContains(response,'Information zur Vollerhebung')
        self.assertNotContains(response,'Evaluieren:')
    
    def test_post_bestellung(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        c.post('/veranstalter/', {'anzahl': 42, 'sprache': 'de', 'typ': 'vu', 'verantwortlich': self.p.id})
        self.v = Veranstaltung.objects.get(id=self.v.id)
        self.assertEqual(self.v.anzahl, 42)
    
    def test_post_bestellung_vollerhebung(self):
        self.s.vollerhebung = True
        self.s.save()
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        # Post mit fehlenden Daten ist nicht valide
        c.post('/veranstalter/', {'anzahl': 42})
        self.v = Veranstaltung.objects.get(id=self.v.id)
        self.assertEqual(self.v.anzahl, None)
        # Post mit allen Daten ist valide
        c.post('/veranstalter/', {'anzahl': 42, 'sprache': 'de',
                                  'typ': 'vu', 
                                  'verantwortlich': self.p.id, 
                                  'ergebnis_empfaenger': {self.p.id},
                                  }
               )
        self.v = Veranstaltung.objects.get(id=self.v.id)
        self.assertEqual(self.v.anzahl, 42)
    
    def test_get_kommentar(self):
        self.s.sichtbarkeit = 'VER'
        self.s.save()
        c = login_veranstalter(self.v)
        response = c.get('/veranstalter/')
        ctx = response.context
        self.assertTrue(isinstance(ctx['comment_form'], KommentarModelForm))
    
    def test_post_kommentar(self):
        c = login_veranstalter(self.v)
        self.s.sichtbarkeit = 'VER'
        self.s.save()
        c.post('/veranstalter/', {'veranstaltung': self.v, 'autor': self.p.id, 'text': 'Toll!'})
        self.v = Veranstaltung.objects.get(id=self.v.id)
        self.assertEqual(self.v.kommentar.text, 'Toll!')
