from django.test import TestCase
from io import BytesIO

from feedback.parser.tan import parse


class TANParserTest(TestCase):
    CSV_FILE = """"Umfrage";"TAN (14-stellig)";"TAN (5-stellig)";"E-Mail";"Teilnahme erfolgt";
"Veranstaltung mit Losung";"LOSUNG";;;;
"Veranstaltung mit TAN";"LangeTAN1";"TAN1";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN2";"TAN2";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN3";"TAN3";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN4";"TAN4";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN5";"TAN5";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN6";"TAN6";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN7";"TAN7";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN8";"TAN8";"";"Nein";
"Veranstaltung mit TAN";"LangeTAN9";"TAN9";"";"Nein";
"""

    def test_parser(self):
        csvfile = BytesIO(self.CSV_FILE.encode('iso-8859-1'))
        tans = parse(csvfile)
        self.assertIsNotNone(tans)

        correct_tan_dict = {
            'Veranstaltung mit Losung': ['LOSUNG'],
            'Veranstaltung mit TAN': [
                'TAN1', 'TAN2', 'TAN3', 'TAN4', 'TAN5', 'TAN6', 'TAN7', 'TAN8',
                'TAN9'
            ]
        }

        self.assertDictEqual(tans, correct_tan_dict)
