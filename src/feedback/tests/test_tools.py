# coding=utf-8

from django.template import Context
from django.test import TestCase

from feedback.models import Fragebogen2009, Ergebnis2009, Fragebogen2012, Ergebnis2012
from feedback.tests.tools import get_veranstaltung
from feedback.tools import get_average, render_email, ean_checksum_calc, ean_checksum_valid


class GetAverageTest(TestCase):
    def setUp(self):
        self.s, self.v = get_veranstaltung('vu')
        self.f = []
        self.f.append(Fragebogen2009.objects.create(veranstaltung=self.v))
        self.f.append(Fragebogen2009.objects.create(veranstaltung=self.v))
        self.f.append(Fragebogen2009.objects.create(veranstaltung=self.v, ue_gesamt=1,
                                                    ue_e=2, ue_f=3,
                                                    ue_a=4, ue_b=5, ue_c=1, ue_d=2,
                                                    ue_g=3, ue_i=4, ue_j=5, ue_k=1))
        self.f.append(Fragebogen2009.objects.create(veranstaltung=self.v, ue_gesamt=2,
                                                    ue_e=3, ue_f=4,
                                                    ue_a=5, ue_b=1, ue_c=2, ue_d=3,
                                                    ue_g=4, ue_i=5, ue_j=1, ue_k=2))

        # Evasys gibt auch den Wert int(0) zurück
        # siehe: https://www.fachschaft.informatik.tu-darmstadt.de/trac/fs/ticket/1192
        self.f2012 = []
        self.f2012.append(Fragebogen2012.objects.create(veranstaltung=self.v,
                                                        ue_7=1, ue_9=1, ue_10=1))
        self.f2012.append(Fragebogen2012.objects.create(veranstaltung=self.v,
                                                        ue_7=2, ue_9=2, ue_10=2))
        self.f2012.append(Fragebogen2012.objects.create(veranstaltung=self.v,
                                                        ue_7=0, ue_9=2, ue_10=2))
        self.f2012.append(Fragebogen2012.objects.create(veranstaltung=self.v,
                                                        ue_7=2, ue_9=0, ue_10=3))
        self.f2012.append(Fragebogen2012.objects.create(veranstaltung=self.v,
                                                        ue_7=3, ue_9=3, ue_10=0))

    def test_single_part(self):
        self.assertSequenceEqual(get_average(Ergebnis2009, self.f, 'ue_gesamt'), [1.5, 2])

    def test_multiple_parts(self):
        self.assertSequenceEqual(get_average(Ergebnis2009, self.f, 'ue_betreuung'), [3, 2])
        self.assertSequenceEqual(get_average(Ergebnis2012, self.f2012, 'ue_betreuung'), [2, 5])

    def test_weighted_parts(self):
        self.assertSequenceEqual(get_average(Ergebnis2009, self.f, 'ue_feedbackpreis'), [2.25, 2])

    def test_empty_sheets(self):
        self.assertSequenceEqual(get_average(Ergebnis2009, [], 'v_feedbackpreis'), [None, 0])
        self.assertSequenceEqual(get_average(Ergebnis2009, self.f[:2], 'v_feedbackpreis'), [None, 0])


class ToolsTest(TestCase):
    def test_render_email(self):
        template = u'Die Antwort ist {{op}} {{antwort}}.'
        context = Context({'op': '>', 'antwort': 41})
        self.assertEqual(render_email(template, context), 'Die Antwort ist > 41.')

        template = u'Das ist {% kein gültiges Template.'
        self.assertEqual(render_email(template, context), '!!! Syntaxfehler im Mailtext !!!')

    def test_ean_calc(self):
        self.assertEqual(ean_checksum_calc(200000151700), 0)
        self.assertEqual(ean_checksum_calc(2000001517000), 0)
        self.assertTrue(ean_checksum_valid(2000001517000))
