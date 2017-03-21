# coding=utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from feedback.models import Semester, Ergebnis2009, Veranstaltung, \
    Kommentar, Person, BarcodeScanner, BarcodeAllowedState

from feedback.tests.test_views_veranstalter import login_veranstalter
from feedback.tests import redirect_urls
import json
from freezegun import freeze_time
import datetime


@override_settings(ROOT_URLCONF=redirect_urls)
class RedirectTest(TestCase):

    def test_redirect(self):
        response = self.client.get('/redirect/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'http://www.d120.de/')

        response = self.client.get('/redirect/fachschaft/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'http://www.d120.de/fachschaft/')


class PublicIndexTest(TestCase):
    def setUp(self):
        User.objects.create_superuser('testuser', None, 'secretpw')
        self.s0 = Semester.objects.create(semester=20105, fragebogen='2009', sichtbarkeit='ADM')
        self.s1 = Semester.objects.create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')
        params = {'semester': self.s1, 'grundstudium': False, 'evaluieren': True, 'lv_nr': '123'}
        self.v0 = Veranstaltung.objects.create(typ='vu', name='Stoning I', **params)
        self.v1 = Veranstaltung.objects.create(typ='vu', name='Stoning II', **params)
        self.e0 = Ergebnis2009.objects.create(veranstaltung=self.v0, anzahl=20,
                                              v_gesamt=2.3, v_gesamt_count=20,
                                              v_didaktik=1.5, v_didaktik_count=3)
        self.e1 = Ergebnis2009.objects.create(veranstaltung=self.v1, anzahl=20,
                                              v_gesamt=1.2, v_gesamt_count=20,
                                              v_didaktik=2.5, v_didaktik_count=10)

    def test_unauth(self):
        # von außerhalb des Uninetzes
        response = self.client.get('/ergebnisse/')
        self.assertEqual(response.templates[0].name, 'public/unauth.html')

    def test_normal(self):
        # aus dem Uninetz ohne sichtbare Veranstaltungen (s1 nur für Admins)
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/', **extra)
        self.assertEqual(response.templates[0].name, 'public/keine_ergebnisse.html')

        # aus dem Uninetz ohne sichtbare Veranstaltungen (s1 nur für Admins und Veranstalter)
        self.s1.sichtbarkeit = 'VER'
        self.s1.save()
        response = self.client.get('/ergebnisse/', **extra)
        self.assertEqual(response.templates[0].name, 'public/keine_ergebnisse.html')

        # aus dem Uninetz, s1 ist sichtbar
        self.s1.sichtbarkeit = 'ALL'
        self.s1.save()
        response = self.client.get('/ergebnisse/', **extra)
        self.assertEqual(response.templates[0].name, 'public/index.html')
        self.assertEqual(response.context['semester'], self.s1)
        self.assertSequenceEqual(response.context['semester_list'], [self.s1])

        # aus dem Uninetz, s1 und s2 sind sichtbar
        self.s0.sichtbarkeit = 'ALL'
        self.s0.save()
        response = self.client.get('/ergebnisse/', **extra)
        self.assertEqual(response.templates[0].name, 'public/index.html')
        ctx = response.context
        self.assertEqual(ctx['semester'], self.s1)
        self.assertSequenceEqual(ctx['semester_list'], [self.s1, self.s0])
        self.assertEqual(ctx['thresh_show'], settings.THRESH_SHOW)
        self.assertEqual(ctx['thresh_valid'], settings.THRESH_VALID)
        self.assertEqual(ctx['order'], 'alpha')
        self.assertEqual(ctx['order_num'], 0)
        self.assertSequenceEqual(ctx['ergebnisse'], [self.e0, self.e1])
        self.assertSequenceEqual(ctx['parts'], Ergebnis2009.parts)
        self.assertEqual(ctx['include_hidden'], False)

        # GET-Parameter: nur semester (Semesterauswahl)
        response = self.client.get('/ergebnisse/', {'semester': self.s0.semester}, **extra)
        self.assertEqual(response.templates[0].name, 'public/index.html')
        ctx = response.context
        self.assertEqual(ctx['semester'], self.s0)
        self.assertSequenceEqual(ctx['semester_list'], [self.s1, self.s0])
        self.assertEqual(ctx['order'], 'alpha')
        self.assertEqual(ctx['order_num'], 0)
        self.assertSequenceEqual(ctx['ergebnisse'], [])
        self.assertSequenceEqual(ctx['parts'], Ergebnis2009.parts)

        # GET-Parameter: nur order
        response = self.client.get('/ergebnisse/', {'order': 'v_gesamt'}, **extra)
        self.assertEqual(response.templates[0].name, 'public/index.html')
        ctx = response.context
        self.assertEqual(ctx['semester'], self.s1)
        self.assertSequenceEqual(ctx['semester_list'], [self.s1, self.s0])
        self.assertEqual(ctx['order'], 'v_gesamt')
        self.assertEqual(ctx['order_num'], 2)
        self.assertSequenceEqual(ctx['ergebnisse'], [self.e1, self.e0])
        self.assertSequenceEqual(ctx['parts'], Ergebnis2009.parts)

        # GET-Parameter: nur order (ungültig)
        response = self.client.get('/ergebnisse/', {'order': 'gibts_nicht'}, **extra)
        self.assertEqual(response.templates[0].name, 'public/index.html')
        ctx = response.context
        self.assertEqual(ctx['order'], 'alpha')
        self.assertEqual(ctx['order_num'], 0)

        # GET-Parameter: semester und order (Sortierung), bei Sortierung ist die geringe Anzahl
        # an Antworten in e0 zu beachten
        self.v0.semester = self.s0
        self.v0.save()
        self.v1.semester = self.s0
        self.v1.save()
        response = self.client.get('/ergebnisse/', {'semester': self.s0.semester, 'order': 'v_didaktik'},
                                   **extra)
        self.assertEqual(response.templates[0].name, 'public/index.html')
        ctx = response.context
        self.assertEqual(ctx['semester'], self.s0)
        self.assertSequenceEqual(ctx['semester_list'], [self.s1, self.s0])
        self.assertEqual(ctx['order'], 'v_didaktik')
        self.assertEqual(ctx['order_num'], 3)
        self.assertSequenceEqual(ctx['ergebnisse'], [self.e1, self.e0])
        self.assertSequenceEqual(ctx['parts'], Ergebnis2009.parts)

    def test_superuser(self):
        self.client.login(username='testuser', password='secretpw')
        response = self.client.get('/intern/ergebnisse/')
        self.assertEqual(response.templates[0].name, 'public/index.html')
        ctx = response.context
        self.assertEqual(ctx['semester'], self.s1)
        self.assertSequenceEqual(ctx['semester_list'], [self.s1, self.s0])
        self.assertSequenceEqual(ctx['ergebnisse'], [self.e0, self.e1])
        self.assertSequenceEqual(ctx['parts'], Ergebnis2009.parts + Ergebnis2009.hidden_parts)
        self.assertEqual(ctx['include_hidden'], True)


class PublicVeranstaltungTest(TestCase):
    def setUp(self):
        User.objects.create_superuser('testuser', None, 'secretpw')
        User.objects.create_user(settings.USERNAME_VERANSTALTER)
        self.s = Semester.objects.create(semester=20110, fragebogen='2009', sichtbarkeit='ADM')
        params = {'semester': self.s, 'grundstudium': False, 'evaluieren': True, 'lv_nr': '123'}
        self.v = Veranstaltung.objects.create(typ='vu', name='Stoning I',
                                              access_token='42', status=Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET, **params)
        self.e = Ergebnis2009.objects.create(veranstaltung=self.v, anzahl=20,
                                             v_gesamt=2.3, v_gesamt_count=20,
                                             v_didaktik=1.5, v_didaktik_count=3)

    def test_unauth(self):
        # von außerhalb des Uninetzes
        response = self.client.get('/ergebnisse/%d/' % self.v.id)
        self.assertEqual(response.templates[0].name, 'public/unauth.html')

    def test_nonexisting(self):
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/1337/', **extra)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.templates[0].name, '404.html')

    def test_unsichtbar_adm(self):
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/%d/' % self.v.id, **extra)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.templates[0].name, '404.html')

    def test_unsichtbar_ver(self):
        self.s.sichtbarkeit = 'VER'
        self.s.save()
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/%d/' % self.v.id, **extra)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.templates[0].name, '404.html')

    def test_vu(self):
        self.s.sichtbarkeit = 'ALL'
        self.s.save()
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/%d/' % self.v.id, **extra)
        ctx = response.context
        self.assertEqual(ctx['v'], self.v)
        with self.assertRaises(KeyError):
            ctx['restricted']
        self.assertEqual(ctx['parts'], list(zip(Ergebnis2009.parts, list(self.e.values()))))
        self.assertEqual(ctx['ergebnis'], self.e)
        with self.assertRaises(KeyError):
            ctx['kommentar']

    def test_v(self):
        self.s.sichtbarkeit = 'ALL'
        self.s.save()
        self.v.typ = 'v'
        self.v.save()
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/%d/' % self.v.id, **extra)
        ctx = response.context
        self.assertEqual(ctx['v'], self.v)
        self.assertEqual(ctx['parts'], list(zip(Ergebnis2009.parts_vl, list(self.e.values()))))
        self.assertEqual(ctx['ergebnis'], self.e)

    def test_kommentar(self):
        self.s.sichtbarkeit = 'ALL'
        self.s.save()
        p = Person.objects.create()
        k = Kommentar.objects.create(veranstaltung=self.v, autor=p, text='Ganz ganz toll!')
        extra = {'REMOTE_ADDR': '130.83.0.1'}
        response = self.client.get('/ergebnisse/%d/' % self.v.id, **extra)
        ctx = response.context
        self.assertEqual(ctx['kommentar'], k)

    def test_veranstalter_adm(self):
        c = login_veranstalter(self.v)
        response = c.get('/ergebnisse/%d/' % self.v.id)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.templates[0].name, '404.html')

    def test_veranstalter_ver(self):
        self.s.sichtbarkeit = 'VER'
        self.s.save()
        c = login_veranstalter(self.v)
        response = c.get('/ergebnisse/%d/' % self.v.id)
        ctx = response.context
        self.assertEqual(ctx['restricted'], True)

    def test_superuser(self):
        self.client.login(username='testuser', password='secretpw')
        response = self.client.get('/ergebnisse/%d/' % self.v.id, **{'REMOTE_USER':'testuser'})
        ctx = response.context
        self.assertEqual(ctx['restricted'], True)


class PublicDropBarcode(TestCase):
    def setUp(self):
        self.path = "/barcodedrop/"
        self.barcode_scanner_no_access_right = BarcodeScanner.objects.create(token="LRh73Ds22", description="")

        self.barcode_scanner = BarcodeScanner.objects.create(token="LRh73Ds23", description="")
        BarcodeAllowedState.objects.create(barcode_scanner=self.barcode_scanner,
                                           allow_state=Veranstaltung.STATUS_GEDRUCKT)
        BarcodeAllowedState.objects.create(barcode_scanner=self.barcode_scanner,
                                           allow_state=Veranstaltung.STATUS_VERSANDT)

        self.semester = Semester.objects.create(semester=20165,
                                                fragebogen='test',
                                                sichtbarkeit='ADM')

        self.veranstaltung = Veranstaltung.objects.create(
            typ='v', name='GDI',
            semester=self.semester,
            grundstudium=False,
            evaluieren=True
        )

        self.deleted_veranstaltung = Veranstaltung.objects.create(
            typ='v', name='GDI2',
            semester=self.semester,
            grundstudium=False,
            evaluieren=True
        )

        self.last_state_veranstaltung = Veranstaltung.objects.create(
            typ='v', name='GDI3',
            semester=self.semester,
            grundstudium=False,
            evaluieren=True,
            status=Veranstaltung.STATUS_BOEGEN_GESCANNT
        )
        self.deleted_barcode = self.deleted_veranstaltung.get_barcode_number()
        self.deleted_veranstaltung.delete()

    def assertJsonSuccess(self, response, success):
        response_json = json.loads(response.content)
        self.assertEqual(response_json['success'], success)

    def test_invalid_token(self):
        response = self.client.post(self.path, {"barcode": 22})
        self.assertJsonSuccess(response, False)

        response = self.client.post(self.path, {"scanner_token": ""})
        self.assertJsonSuccess(response, False)

    def test_invalid_barcode(self):
        response = self.client.post(self.path, {"scanner_token": self.barcode_scanner.token})
        self.assertJsonSuccess(response, False)

        response = self.client.post(self.path, {"barcode": 22, "scanner_token": self.barcode_scanner.token})
        self.assertJsonSuccess(response, False)

        response = self.client.post(self.path, {
            "barcode": self.deleted_barcode,
            "scanner_token": self.barcode_scanner.token
        })
        self.assertJsonSuccess(response, False)

    def test_barcode_scanner_right(self):
        barcode = self.veranstaltung.get_barcode_number()
        response = self.client.post(self.path, {
            "barcode": barcode,
            "scanner_token": self.barcode_scanner_no_access_right.token
        })
        self.assertJsonSuccess(response, False)
        
        barcode = self.last_state_veranstaltung.get_barcode_number()
        response = self.client.post(self.path, {
            "barcode": barcode,
            "scanner_token": self.barcode_scanner.token
        })
        self.assertJsonSuccess(response, False)

    def test_valid_barcode_scan(self):
        barcode = self.veranstaltung.get_barcode_number()
        response = self.client.post(self.path, {
            "barcode": barcode,
            "scanner_token": self.barcode_scanner.token
        })
        self.assertJsonSuccess(response, True)
        self.veranstaltung.refresh_from_db()
        self.assertEqual(self.veranstaltung.status, Veranstaltung.STATUS_GEDRUCKT)

    def test_double_scan(self):
        barcode = self.veranstaltung.get_barcode_number()
        response = self.client.post(self.path, {
            "barcode": barcode,
            "scanner_token": self.barcode_scanner.token
        })
        self.assertJsonSuccess(response, True)

        response = self.client.post(self.path, {
            "barcode": barcode,
            "scanner_token": self.barcode_scanner.token
        })
        self.assertJsonSuccess(response, False)

    def test_valid_double_scan(self):
        barcode = self.veranstaltung.get_barcode_number()
        response = self.client.post(self.path, {
            "barcode": barcode,
            "scanner_token": self.barcode_scanner.token
        })
        self.assertJsonSuccess(response, True)

        future_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
        with freeze_time(future_time):
            response = self.client.post(self.path, {
                "barcode": barcode,
                "scanner_token": self.barcode_scanner.token
            })
            self.assertJsonSuccess(response, True)
