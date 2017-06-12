# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from feedback.models import Einstellung, Person, Veranstaltung, Tutor
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
        self.p = Person.objects.create(vorname="v1", nachname="n1", email="v1n1@fb.de", anschrift="Strasse")
        self.p2 = Person.objects.create(vorname="v2", nachname="n2")
        self.p3 = Person.objects.create(vorname="v3", nachname="n3")

        self.v.veranstalter.add(self.p)
        self.v.veranstalter.add(self.p2)

        self.v.ergebnis_empfaenger.add(self.p)
        self.v.ergebnis_empfaenger.add(self.p2)

        self.v.primaerdozent = self.p
        self.v.verantwortlich = self.p
        self.v.save()

        self.s2, self.v_wo_excercises = get_veranstaltung('v')
        self.v_wo_excercises.veranstalter.add(self.p3)
    
    def test_unauth(self):
        response = self.client.get('/veranstalter/')
        self.assertEqual(response.templates[0].name, 'veranstalter/not_authenticated.html')

    def test_invalid_state(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='0')
        c = login_veranstalter(self.v)
        self.v.status = Veranstaltung.STATUS_GEDRUCKT
        self.v.save()
        response = c.get('/veranstalter/bestellung')
        self.assertEqual(302, response.status_code)

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

    def test_post_bestellung(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response_first_step = c.post('/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                        "veranstalter_wizard-current_step": "evaluation"})

        self.assertTemplateUsed(response_first_step, "formtools/wizard/basisdaten.html")

        response_second_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-anzahl": 22,
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": [self.p.id, self.p2.id],
            "save": "Speichern"
        })

        self.assertTemplateUsed(response_second_step, "formtools/wizard/primaerdozent.html")

        response_third_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "primaerdozent",
            "primaerdozent-primaerdozent": self.p.id
        })

        self.assertTemplateUsed(response_third_step, "formtools/wizard/address.html")

        response_fourth_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "verantwortlicher_address",
            "verantwortlicher_address-email": "test@test.de",
            "verantwortlicher_address-anschrift": "Alexanderstrasse 8, 64287 Darmstadt"
        })

        self.assertTemplateUsed(response_fourth_step, "formtools/wizard/freiefragen.html")

        response_fifth_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        self.assertTemplateUsed(response_fifth_step, "formtools/wizard/tutoren.html")

        self.assertEqual(Tutor.objects.count(), 0)
        response_sixth_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "tutoren",
            "tutoren-csv_tutoren": "Müller,Max,muller.max@web.de,Bemerkung1\nMustermann,Erika,erika.mustermann@aa.de"
        })

        self.assertTemplateUsed(response_sixth_step, "formtools/wizard/veroeffentlichen.html")

        response_seventh_step = c.post('/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                    "veranstalter_wizard-current_step": "veroeffentlichen"})

        self.assertTemplateUsed(response_seventh_step, "formtools/wizard/zusammenfassung.html")

        response_eight_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTemplateUsed(response_eight_step, "formtools/wizard/bestellung_done.html")

        self.assertTrue(self.v.evaluieren)
        self.assertEqual(self.v.primaerdozent, self.p)
        self.assertEqual(Tutor.objects.count(), 2)
        self.assertEqual(self.p.email, "test@test.de")
        self.assertEqual(self.v.anzahl, 22)
        self.assertEqual(self.v.ergebnis_empfaenger.count(), 2)
        self.assertEqual(self.v.sprache, "de")

    def test_missing_sessionid(self):
        c = login_veranstalter(self.v)
        del c.cookies['sessionid']
        response = c.post('/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                        "veranstalter_wizard-current_step": "evaluation"})
        self.assertEqual(response.status_code, 404)
    
    def test_post_keine_evaluation(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response_firststep = c.post('/veranstalter/bestellung', {"evaluation-evaluieren": False,
                                                        "veranstalter_wizard-current_step": "evaluation"})
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")
        response_second = c.post('/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertTemplateUsed(response_second, "formtools/wizard/bestellung_done.html")
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")
    
    def test_post_bestellung_vollerhebung(self):
        self.s.vollerhebung = True
        self.s.save()
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)

        response_vollerhebung = c.get('/veranstalter/bestellung')

        self.assertContains(response_vollerhebung, "<h2>Information zur Vollerhebung</h2>")

        response_firststep = c.post('/veranstalter/bestellung', {"evaluation-evaluieren": True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/basisdaten.html")

    def test_post_access_bestellung(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        self.v.status = Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR
        self.v.save()

        c = login_veranstalter(self.v)

        response_firststep = c.post('/veranstalter/bestellung', {
            'evaluation-evaluieren': True,
            "veranstalter_wizard-current_step": "evaluation"
        })

        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/basisdaten.html")

    def test_post_bestellung_ein_ergebnis_empfaenger(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)
        response_firststep = c.post('/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        self.assertTemplateUsed(response_firststep, "formtools/wizard/basisdaten.html")

        response_secondstep = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-anzahl": 22,
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": self.p2.id,
            "save": "Speichern"
        })

        self.assertTemplateUsed(response_secondstep, "formtools/wizard/address.html")

        response_fourth_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "verantwortlicher_address",
            "verantwortlicher_address-email": "test@test.de",
            "verantwortlicher_address-anschrift": "Alexanderstrasse 8, 64287 Darmstadt"
        })

        self.assertTemplateUsed(response_fourth_step, "formtools/wizard/freiefragen.html")

        response_fifth_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        self.assertTemplateUsed(response_fifth_step, "formtools/wizard/tutoren.html")

        self.assertEqual(Tutor.objects.count(), 0)
        response_sixth_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "tutoren",
            "tutoren-csv_tutoren": "Müller,Max,muller.max@web.de,Bemerkung1\nMustermann,Erika,erika.mustermann@aa.de"
        })
        self.assertTemplateUsed(response_sixth_step, "formtools/wizard/veroeffentlichen.html")

        response_seventh_step = c.post('/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                    "veranstalter_wizard-current_step": "veroeffentlichen"})

        self.assertTemplateUsed(response_seventh_step, "formtools/wizard/zusammenfassung.html")

        response_eight_step = c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTemplateUsed(response_eight_step, "formtools/wizard/bestellung_done.html")
        self.assertTrue(self.v.evaluieren)
        self.assertEqual(self.v.primaerdozent, self.p2)
        self.assertEqual(Tutor.objects.count(), 2)
        self.assertEqual(self.p.email, "test@test.de")

    def test_post_bestellung_without_excercises(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v_wo_excercises)
        c.post('/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "v",
            "basisdaten-anzahl": 11,
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p3.id,
            "basisdaten-ergebnis_empfaenger": self.p3.id,
            "save": "Speichern"
        })
        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "verantwortlicher_address",
            "verantwortlicher_address-email": "test@test.de",
            "verantwortlicher_address-anschrift": "Alexanderstrasse 8, 64287 Darmstadt"
        })
        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })
        response_fourth_step = c.post('/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                  "veranstalter_wizard-current_step": "veroeffentlichen"})
        self.assertEqual(Tutor.objects.count(), 0)

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTemplateUsed(response_fourth_step, "formtools/wizard/zusammenfassung.html")
        self.assertEqual(Tutor.objects.count(), 0)

    def test_status_changes(self):
        Einstellung.objects.create(name='bestellung_erlaubt', wert='1')
        c = login_veranstalter(self.v)

        c.post('/veranstalter/bestellung', {"evaluation-evaluieren": False,
                                                                 "veranstalter_wizard-current_step": "evaluation"})

        c.post('/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)

        c.post('/veranstalter/bestellung', {
            'evaluation-evaluieren': True,
            "veranstalter_wizard-current_step": "evaluation"})

        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-anzahl": 22,
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": [self.p.id, self.p2.id],
            "save": "Speichern"
        })

        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "primaerdozent",
            "primaerdozent-primaerdozent": self.p.id
        })

        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "verantwortlicher_address",
            "verantwortlicher_address-email": "test@test.de",
            "verantwortlicher_address-anschrift": "Alexanderstrasse 8, 64287 Darmstadt"
        })

        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "tutoren",
            "tutoren-csv_tutoren": "Müller,Max,muller.max@web.de,Bemerkung1\nMustermann,Erika,erika.mustermann@aa.de"
        })

        c.post('/veranstalter/bestellung', {
            'veroeffentlichen-veroeffentlichen': True,
            "veranstalter_wizard-current_step": "veroeffentlichen"})


        c.post('/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTrue(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR)

        c.post('/veranstalter/bestellung', {"evaluation-evaluieren": False,
                                            "veranstalter_wizard-current_step": "evaluation"})

        c.post('/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)


