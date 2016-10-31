# coding=utf-8

from django.conf import settings
from django.test import TestCase

from feedback.models import Semester, Veranstaltung, Fragebogen2008, Fragebogen2009, Fragebogen2012, Fragebogen2016
from feedback.parser.ergebnisse import parse_ergebnisse
from feedback.parser.ergebnisse.parser import Parser


class ParserTest(TestCase):
    def _do_mapping_test(self, fun, mapping):
        for key, value in mapping.items() + [('asdfjkl', '')]:
            self.assertEqual(fun(key), value)

    def test_parse_fach(self):
        self._do_mapping_test(Parser.parse_fach, {'1': 'inf', '2': 'winf', '3': 'math',
                                                  '4': 'etit', '5': 'ist', '6': 'ce', '7': 'sonst'})

    def test_parse_abschluss(self):
        self._do_mapping_test(Parser.parse_abschluss, {'1': 'bsc', '2': 'msc', '3': 'dipl',
                                                       '4': 'lehr', '5': 'sonst'})

    def test_parse_geschwindigkeit(self):
        self._do_mapping_test(Parser.parse_geschwindigkeit, {'1': 's', '2': 'l'})

    def test_parse_niveau(self):
        self._do_mapping_test(Parser.parse_niveau, {'1': 'h', '2': 'n'})

    def test_parse_empfehlung(self):
        self._do_mapping_test(Parser.parse_empfehlung, {'1': 'j', '2': 'n'})

    def test_parse_boolean(self):
        self._do_mapping_test(Parser.parse_boolean, {'1': 'j', '0': 'n'})

    def test_parse_int(self):
        self.assertEqual(Parser.parse_int(''), None)
        self.assertEqual(Parser.parse_int('42'), 42)

    def _do_parse_ergebnisse_test(self, semester, fragebogen, fb_model):
        s = Semester.objects.create(semester=semester, fragebogen=fragebogen, sichtbarkeit='ADM')
        v = []
        default_params = {'semester': s, 'grundstudium': False, 'evaluieren': True}
        v.append(Veranstaltung.objects.create(name='Test I', lv_nr='1', **default_params))
        v.append(Veranstaltung.objects.create(name='LV-Nr. existiert nicht', lv_nr='4711', **default_params))
        v.append(Veranstaltung.objects.create(name='Test II', lv_nr='1234', **default_params))
        v.append(Veranstaltung.objects.create(name='Ergebnis bereits importiert', lv_nr='9876', **default_params))
        fb_model.objects.create(veranstaltung=v[3])

        testdata = settings.TESTDATA_PATH + 'ergebnis_test_%u.csv' % semester
        with open(testdata, 'r') as f:
            warnings, errors, vcount, fbcount = parse_ergebnisse(s, f)
        self.assertEqual(len(warnings), 2)
        self.assertIn(u'Die Veranstaltung "LV-Nr. existiert nicht" hat in der ' + \
                      'Datenbank die Lehrveranstaltungsnummer "4711", in der CSV-Datei aber ' + \
                      '"2342". Die Ergebnisse wurden trotzdem importiert.', warnings)
        self.assertIn(u'Die Veranstaltung mit der Lehrveranstaltungsnummer ' + \
                      '"1234" hat in der Datenbank den Namen "Test II", in der ' + \
                      'CSV-Datei aber "V.-Name existiert nicht". Die ' + \
                      'Ergebnisse wurden trotzdem importiert.', warnings)
        self.assertEqual(vcount, 3)
        self.assertEqual(fbcount, 4)

        self.assertEqual(len(errors), 2)
        self.assertIn(u'Die Veranstaltung "V. existiert nicht" (1337) ' + \
                      'existiert im System nicht und wurde deshalb nicht importiert!', errors)
        self.assertIn(u'In der Datenbank existieren bereits Fragebögen zur Veranstaltung ' + \
                      '"Ergebnis bereits importiert". Sie wurde deshalb nicht importiert!', errors)

    def test_parse_ergebnisse2008(self):
        self._do_parse_ergebnisse_test(20085, '2008', Fragebogen2008)

    def test_parse_ergebnisse2009(self):
        self._do_parse_ergebnisse_test(20115, '2009', Fragebogen2009)

    def test_parse_ergebnisse2012(self):
        self._do_parse_ergebnisse_test(20125, '2012', Fragebogen2012)

    def test_parse_ergebnisse2016(self):
        self._do_parse_ergebnisse_test(20155, '2016', Fragebogen2016)
