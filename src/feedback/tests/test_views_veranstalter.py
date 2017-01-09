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
    
    # def test_get_bestellung(self):
    #     Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
    #     c = login_veranstalter(self.v)
    #     response = c.get('/veranstalter/')
    #     ctx = response.context
    #     self.assertTrue(isinstance(ctx['order_form'], BestellungModelForm))
    #     self.assertNotContains(response,'Information zur Vollerhebung')
    #     self.assertContains(response,'Evaluieren:')
        
    # def test_get_bestellung_vollerhebung(self):
    #     """Teste ob der Hinweis zur Vollerhebung angezeigt wird und ein Austragen
    #     nicht möglich ist"""
    #     self.s.vollerhebung = True
    #     self.s.save()
    #     Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
    #     c = login_veranstalter(self.v)
    #     response = c.get('/veranstalter/')
    #     ctx = response.context
    #     self.assertTrue(isinstance(ctx['order_form'], BestellungModelForm))
    #     self.assertContains(response,'Information zur Vollerhebung')
    #     self.assertNotContains(response,'Evaluieren:')
    
    def test_post_bestellung(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response_firststep = c.post('/veranstalter/', {'evaluation-evaluieren': True,
                                  "veranstalter_wizard-current_step": "evaluation"})
        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")

    def test_post_keine_evaluation(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response_firststep = c.post('/veranstalter/', {"veranstalter_wizard-current_step": "evaluation"})

        self.v.refresh_from_db()
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")
    
    def test_post_bestellung_vollerhebung(self):
        self.s.vollerhebung = True
        self.s.save()
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)

        response_vollerhebung = c.get('/veranstalter/')

        self.assertContains(response_vollerhebung, "<h2>Information zur Vollerhebung</h2>")

        response_firststep = c.post('/veranstalter/', {"evaluation-evaluieren": True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        self.v.refresh_from_db()
        self.assertEqual(self.v.status, Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR)
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")

    def test_post_access_bestellung(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        self.v.status = Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR
        self.v.save()

        c = login_veranstalter(self.v)

        response_firststep = c.post('/veranstalter/', {'evaluation-evaluieren': True,
                                  "veranstalter_wizard-current_step": "evaluation"})
        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")

