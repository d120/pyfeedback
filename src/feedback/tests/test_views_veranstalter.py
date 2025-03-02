# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from feedback.models import Person, Veranstaltung, Tutor
from feedback.tests.tools import get_veranstaltung, login_veranstalter
from django.utils.translation import get_language

class VeranstalterLoginTest(TestCase):
    def setUp(self):
        _, self.v = get_veranstaltung('vu')
        User.objects.create_user(settings.USERNAME_VERANSTALTER)

    def test_incomplete_params(self):
        response = self.client.get(f'/{get_language()}/veranstalter/login/')
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')

        response = self.client.get(f'/{get_language()}/veranstalter/login/', {'vid': self.v.id})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')

        response = self.client.get(f'/{get_language()}/veranstalter/login/', {'token': self.v.access_token})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')

    def test_bad_params(self):
        response = self.client.get(f'/{get_language()}/veranstalter/login/', {'vid': self.v.id, 'token': 'inkorrekt'})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')

        response = self.client.get(f'/{get_language()}/veranstalter/login/', {'vid': 123, 'token': self.v.access_token})
        self.assertEqual(response.templates[0].name, 'veranstalter/login_failed.html')

    def test_ok(self):
        response = self.client.get(f'/{get_language()}/veranstalter/login/', {'vid': self.v.id,
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
        response = self.client.get(f'/{get_language()}/veranstalter/')
        self.assertEqual(response.templates[0].name, 'veranstalter/not_authenticated.html')

    def test_invalid_state(self):
        c = login_veranstalter(self.v)
        self.v.status = Veranstaltung.STATUS_GEDRUCKT
        self.v.save()
        response = c.get(f'/{get_language()}/veranstalter/bestellung')
        self.assertEqual(302, response.status_code)

    def test_nothing(self):
        c = login_veranstalter(self.v)
        response = c.get(f'/{get_language()}/veranstalter/')
        ctx = response.context
        self.assertEqual(ctx['veranstaltung'], self.v)
        with self.assertRaises(KeyError):
            ctx['order_form']
        with self.assertRaises(KeyError):
            ctx['comment_form']

    def test_post_bestellung(self):
        c = login_veranstalter(self.v)

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'anzahl-anzahl': 12,
                                                        "veranstalter_wizard-current_step": "anzahl"})
        
        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")
        
        response_first_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                        "veranstalter_wizard-current_step": "evaluation"})

        self.assertTemplateUsed(response_first_step, "formtools/wizard/basisdaten.html")

        response_second_temp_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": [self.p.id, self.p2.id],
            "basisdaten-auswertungstermin": '2011-01-01',
            "basisdaten-digitale_eval": "on",
            "save": "Speichern"
        })

        self.assertTemplateUsed(response_second_temp_step, "formtools/wizard/digitale_evaluation.html")

        response_second_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "digitale_eval",
            "digitale_eval-digitale_eval_type": "T",
        })
        
        # "primaerdozent" is removed

        # "verantwortlicher_address" is removed

        self.assertTemplateUsed(response_second_step, "formtools/wizard/freiefragen.html")

        response_fifth_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        self.assertEqual(Tutor.objects.count(), 0)

        # step "tutoren" is removed

        self.assertTemplateUsed(response_fifth_step, "formtools/wizard/veroeffentlichen.html")

        response_seventh_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                    "veranstalter_wizard-current_step": "veroeffentlichen"})

        self.assertTemplateUsed(response_seventh_step, "formtools/wizard/zusammenfassung.html")

        response_eight_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTemplateUsed(response_eight_step, "formtools/wizard/bestellung_done.html")

        self.assertTrue(self.v.evaluieren)
        # step "primaerdozent" removed
        self.assertEqual(Tutor.objects.count(), 0) # step "tutoren" removed
        self.assertEqual(self.p.email, "v1n1@fb.de") # step "verantwortlicher_address" removed
        self.assertEqual(self.v.anzahl, 12)
        self.assertEqual(self.v.ergebnis_empfaenger.count(), 2)
        self.assertEqual(self.v.sprache, "de")

    def test_missing_sessionid(self):
        c = login_veranstalter(self.v)
        del c.cookies[settings.SESSION_COOKIE_NAME]
        response = c.post(f'/{get_language()}/veranstalter/bestellung', {'anzahl-anzahl': 12,
                                                        "veranstalter_wizard-current_step": "anzahl"})
        self.assertEqual(response.status_code, 404)

    def test_post_keine_evaluation(self):
        c = login_veranstalter(self.v)

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": 12,
                                                        "veranstalter_wizard-current_step": "anzahl"})
        
        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")
        
        response_firststep = c.post(f'/{get_language()}/veranstalter/bestellung', {"evaluation-evaluieren": False,
                                                        "veranstalter_wizard-current_step": "evaluation"})
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")
        response_second = c.post(f'/{get_language()}/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertTemplateUsed(response_second, "formtools/wizard/bestellung_done.html")
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")

    def test_post_bestellung_vollerhebung(self):
        self.s.vollerhebung = True
        self.s.save()
        c = login_veranstalter(self.v)

        response_vollerhebung = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": 12,
                                                       "veranstalter_wizard-current_step": "anzahl"})

        self.assertContains(response_vollerhebung, "<h2>Information zur Vollerhebung</h2>")
        self.assertTemplateUsed(response_vollerhebung, "formtools/wizard/evaluation.html")

        response_firststep = c.post(f'/{get_language()}/veranstalter/bestellung', {"evaluation-evaluieren": True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/basisdaten.html")


        ### test anzahl less than MIN_BESTELLUNG_ANZAHL ###

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": Veranstaltung.MIN_BESTELLUNG_ANZAHL - 1,
                                                       "veranstalter_wizard-current_step": "anzahl"})

        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")

        response_firststep = c.post(f'/{get_language()}/veranstalter/bestellung', {"veranstalter_wizard-current_step": "evaluation"})
        
        self.assertTemplateUsed(response_firststep, "formtools/wizard/zusammenfassung.html")

        c.post(f'/{get_language()}/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertFalse(self.v.evaluieren)


        ### test anzahl more than or equal to MIN_BESTELLUNG_ANZAHL ###

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": Veranstaltung.MIN_BESTELLUNG_ANZAHL + 1,
                                                       "veranstalter_wizard-current_step": "anzahl"})

        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")

        response_first_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                        "veranstalter_wizard-current_step": "evaluation"})

        self.assertTemplateUsed(response_first_step, "formtools/wizard/basisdaten.html")

        response_second_temp_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": [self.p.id, self.p2.id],
            "basisdaten-auswertungstermin": '2011-01-01',
            "basisdaten-digitale_eval": "on",
            "save": "Speichern"
        })

        self.assertTemplateUsed(response_second_temp_step, "formtools/wizard/digitale_evaluation.html")

        response_second_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "digitale_eval",
            "digitale_eval-digitale_eval_type": "T",
        })

        self.assertTemplateUsed(response_second_step, "formtools/wizard/freiefragen.html")

        response_fifth_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        self.assertTemplateUsed(response_fifth_step, "formtools/wizard/veroeffentlichen.html")

        response_seventh_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                    "veranstalter_wizard-current_step": "veroeffentlichen"})

        self.assertTemplateUsed(response_seventh_step, "formtools/wizard/zusammenfassung.html")

        response_eight_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.assertTemplateUsed(response_eight_step, "formtools/wizard/bestellung_done.html")

        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertEqual(self.v.anzahl, Veranstaltung.MIN_BESTELLUNG_ANZAHL + 1)
        self.assertEqual(self.v.ergebnis_empfaenger.count(), 2)
        self.assertEqual(self.v.sprache, "de")

    def test_post_access_bestellung(self):
        self.v.status = Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR
        self.v.save()

        c = login_veranstalter(self.v)

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            'anzahl-anzahl': 12,
            "veranstalter_wizard-current_step": "anzahl"
        })

        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")

        response_firststep = c.post(f'/{get_language()}/veranstalter/bestellung', {
            'evaluation-evaluieren': True,
            "veranstalter_wizard-current_step": "evaluation"
        })

        self.v.refresh_from_db()
        self.assertTrue(self.v.evaluieren)
        self.assertTemplateUsed(response_firststep, "formtools/wizard/basisdaten.html")

    def test_post_bestellung_ein_ergebnis_empfaenger(self):
        c = login_veranstalter(self.v)
        
        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'anzahl-anzahl': 12,
                                                       "veranstalter_wizard-current_step": "anzahl"})
        
        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")
        
        response_firststep = c.post(f'/{get_language()}/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        self.assertTemplateUsed(response_firststep, "formtools/wizard/basisdaten.html")

        response_second_temp_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": self.p2.id,
            "basisdaten-auswertungstermin": '2011-01-01',
            "basisdaten-digitale_eval": "on",
            "save": "Speichern"
        })

        self.assertTemplateUsed(response_second_temp_step, "formtools/wizard/digitale_evaluation.html")

        response_secondstep = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "digitale_eval",
            "digitale_eval-digitale_eval_type": "T",
        })

        # "verantwortlicher_address" is removed

        self.assertTemplateUsed(response_secondstep, "formtools/wizard/freiefragen.html")

        response_fifth_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        self.assertEqual(Tutor.objects.count(), 0)
        
        # step 6 "tutoren" is removed

        self.assertTemplateUsed(response_fifth_step, "formtools/wizard/veroeffentlichen.html")

        response_seventh_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                    "veranstalter_wizard-current_step": "veroeffentlichen"})

        self.assertTemplateUsed(response_seventh_step, "formtools/wizard/zusammenfassung.html")

        response_eight_step = c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTemplateUsed(response_eight_step, "formtools/wizard/bestellung_done.html")
        self.assertTrue(self.v.evaluieren)
        # step "primaerdozent" removed
        self.assertEqual(Tutor.objects.count(), 0) # step "tutoren" removed
        self.assertEqual(self.p.email, "v1n1@fb.de") # step "verantwortlicher_address" removed

    def test_post_bestellung_without_excercises(self):
        c = login_veranstalter(self.v_wo_excercises)

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'anzahl-anzahl': 12,
                                                       "veranstalter_wizard-current_step": "anzahl"})
        
        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")
        
        c.post(f'/{get_language()}/veranstalter/bestellung', {'evaluation-evaluieren': True,
                                                       "veranstalter_wizard-current_step": "evaluation"})

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "v",
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p3.id,
            "basisdaten-ergebnis_empfaenger": self.p3.id,
            "save": "Speichern"
        })

        # "verantwortlicher_address" is removed

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })
        response_fourth_step = c.post(f'/{get_language()}/veranstalter/bestellung', {'veroeffentlichen-veroeffentlichen': True,
                                  "veranstalter_wizard-current_step": "veroeffentlichen"})
        self.assertEqual(Tutor.objects.count(), 0)

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTemplateUsed(response_fourth_step, "formtools/wizard/zusammenfassung.html")
        self.assertEqual(Tutor.objects.count(), 0)

    def test_status_changes(self):
        c = login_veranstalter(self.v)

        c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": 12,
                                                                 "veranstalter_wizard-current_step": "anzahl"})

        c.post(f'/{get_language()}/veranstalter/bestellung', {"evaluation-evaluieren": False,
                                                                 "veranstalter_wizard-current_step": "evaluation"})

        c.post(f'/{get_language()}/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            'anzahl-anzahl': 12,
            "veranstalter_wizard-current_step": "anzahl"})
        
        c.post(f'/{get_language()}/veranstalter/bestellung', {
            'evaluation-evaluieren': True,
            "veranstalter_wizard-current_step": "evaluation"})

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "basisdaten",
            "basisdaten-typ": "vu",
            "basisdaten-sprache": "de",
            "basisdaten-verantwortlich": self.p.id,
            "basisdaten-ergebnis_empfaenger": [self.p.id, self.p2.id],
            "basisdaten-auswertungstermin": '2011-01-01',
            "basisdaten-digitale_eval": "on",
            "save": "Speichern"
        })

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "digitale_eval",
            "digitale_eval-digitale_eval_type": "T",
        })

        # "primaerdozent" is removed

        # "verantwortlicher_address" is removed

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "freie_fragen",
            "freie_fragen-freifrage1": "Ist das die erste Frage?",
            "freie_fragen-freifrage2": "Ist das die zweite Frage?"
        })

        # step "tutoren" removed

        c.post(f'/{get_language()}/veranstalter/bestellung', {
            'veroeffentlichen-veroeffentlichen': True,
            "veranstalter_wizard-current_step": "veroeffentlichen"})


        c.post(f'/{get_language()}/veranstalter/bestellung', {
            "veranstalter_wizard-current_step": "zusammenfassung"
        })

        self.v.refresh_from_db()
        self.p.refresh_from_db()

        self.assertTrue(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR)

        c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": 12,
                                            "veranstalter_wizard-current_step": "anzahl"})
        
        c.post(f'/{get_language()}/veranstalter/bestellung', {"evaluation-evaluieren": False,
                                            "veranstalter_wizard-current_step": "evaluation"})

        c.post(f'/{get_language()}/veranstalter/bestellung', {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v.refresh_from_db()
        self.assertFalse(self.v.evaluieren)
        self.assertEqual(self.v.status, Veranstaltung.STATUS_KEINE_EVALUATION)


    def test_post_bestellung_with_digital(self):
        c = login_veranstalter(self.v_wo_excercises)

        response_initial_step = c.post(
            f'/{get_language()}/veranstalter/bestellung', {
                'anzahl-anzahl': 12,
                "veranstalter_wizard-current_step": "anzahl"
            })
        
        self.assertTemplateUsed(response_initial_step, "formtools/wizard/evaluation.html")
        
        c.post(
            f'/{get_language()}/veranstalter/bestellung', {
                'evaluation-evaluieren': True,
                "veranstalter_wizard-current_step": "evaluation"
            })

        response = c.post(
            f'/{get_language()}/veranstalter/bestellung', {
                "veranstalter_wizard-current_step": "basisdaten",
                "basisdaten-typ": "v",
                "basisdaten-sprache": "de",
                "basisdaten-verantwortlich": self.p3.id,
                "basisdaten-ergebnis_empfaenger": self.p3.id,
                "basisdaten-digitale_eval": 'on',
                "basisdaten-auswertungstermin": "2011-01-01",
                "save": "Speichern"
            })

        self.assertTemplateUsed(response,
                                "formtools/wizard/digitale_evaluation.html")

        response = c.post(
            f'/{get_language()}/veranstalter/bestellung', {
                "veranstalter_wizard-current_step": "digitale_eval",
                "digitale_eval-digitale_eval_type": "L",
            })

        self.assertTemplateUsed(response, "formtools/wizard/freiefragen.html")

        # step "verantwortlicher_address" removed 

        c.post(
            f'/{get_language()}/veranstalter/bestellung', {
                "veranstalter_wizard-current_step": "freie_fragen",
                "freie_fragen-freifrage1": "Ist das die erste Frage?",
                "freie_fragen-freifrage2": "Ist das die zweite Frage?"
            })
        c.post(
            f'/{get_language()}/veranstalter/bestellung', {
                'veroeffentlichen-veroeffentlichen': True,
                "veranstalter_wizard-current_step": "veroeffentlichen"
            })

        c.post(f'/{get_language()}/veranstalter/bestellung',
               {"veranstalter_wizard-current_step": "zusammenfassung"})

        self.v_wo_excercises.refresh_from_db()
        self.assertEqual(self.v_wo_excercises.digitale_eval_type, 'L')


    def test_evaluation_option_present(self) :
        c = login_veranstalter(self.v)

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": Veranstaltung.MIN_BESTELLUNG_ANZAHL - 1,
                                                    "veranstalter_wizard-current_step": "anzahl"})

        self.assertNotContains(response_initial_step, '<legend class="required">Evaluieren:</legend>')

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": Veranstaltung.MIN_BESTELLUNG_ANZAHL + 1,
                                                    "veranstalter_wizard-current_step": "anzahl"})
        
        self.assertContains(response_initial_step, '<legend class="required">Evaluieren:</legend>')


    def test_evaluation_option_present_vollerhebung(self) :
        self.s.vollerhebung = True
        self.s.save()
        c = login_veranstalter(self.v)

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": Veranstaltung.MIN_BESTELLUNG_ANZAHL - 1,
                                                       "veranstalter_wizard-current_step": "anzahl"})

        self.assertNotContains(response_initial_step, '<legend class="required">Evaluieren:</legend>')

        response_initial_step = c.post(f'/{get_language()}/veranstalter/bestellung', {"anzahl-anzahl": Veranstaltung.MIN_BESTELLUNG_ANZAHL + 1,
                                                       "veranstalter_wizard-current_step": "anzahl"})
        
        self.assertNotContains(response_initial_step, '<legend class="required">Evaluieren:</legend>')