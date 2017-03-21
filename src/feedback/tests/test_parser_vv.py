# coding=utf-8

from django.conf import settings
from django.test import TransactionTestCase

from feedback.models import ImportPerson, ImportCategory, ImportVeranstaltung
from feedback.parser.vv import parse_vv_xml, parse_vv_clear, parse_instructors


class VvParserTest(TransactionTestCase):
    def test_parse_vv_clear(self):
        ImportPerson.objects.create(vorname='Brian', nachname='Cohen')
        c = ImportCategory.objects.create(name='Monty Python')
        ImportVeranstaltung.objects.create(typ='vu', name='Stoning I', category=c)

        parse_vv_clear()

        self.assertFalse(ImportPerson.objects.exists())
        self.assertFalse(ImportCategory.objects.exists())
        self.assertFalse(ImportVeranstaltung.objects.exists())

    def test_parse_instructors(self):
        p = []
        self.assertSequenceEqual(parse_instructors(''), [])
        self.assertSequenceEqual(parse_instructors(' \t'), [])

        p.append(ImportPerson.objects.create(nachname='Jemand'))
        self.assertSequenceEqual(parse_instructors('Jemand'), p)

        p.append(ImportPerson.objects.create(vorname='Brian', nachname='Cohen'))
        p.append(ImportPerson.objects.create(vorname='Anna Maria', nachname='Musterfrau'))
        self.assertSequenceEqual(parse_instructors('Jemand; Brian Cohen; Anna Maria Musterfrau'), p)

    def _get_cat_or_fail(self, name, parent):
        try:
            return ImportCategory.objects.get(name=name, parent=parent)
        except ImportCategory.DoesNotExist:
            self.fail('Kategorie "%s" (parent="%s") konnte nicht importiert werden.' % (name, parent))

    def _get_veranst_or_fail(self, typ, name, cat):
        try:
            return ImportVeranstaltung.objects.get(typ=typ, name=name, category=cat)
        except ImportVeranstaltung.DoesNotExist:
            self.fail('Veranstaltung "%s" (category="%s") konnte nicht importiert werden.' % (name, cat))

    def _parse_vv_xml(self, xmltestfile):
        parse_vv_xml(settings.TESTDATA_PATH + xmltestfile)

        cat_root = self._get_cat_or_fail(name='root', parent=None)
        cat_ov = self._get_cat_or_fail(name='Alle Orientierungs- und Einführungsveranstaltungen',
                                       parent=cat_root)
        cat_fb20 = self._get_cat_or_fail(name='FB20 - Informatik', parent=cat_root)
        cat_fb20_ov = self._get_cat_or_fail(name='Orientierungsveranstaltungen', parent=cat_fb20)
        cat_fb20_g = self._get_cat_or_fail(name='Grundlagenveranstaltungen', parent=cat_fb20)
        self.assertEqual(ImportCategory.objects.count(), 5)

        self.assertEqual(cat_root.ivs.count(), 0)
        self.assertEqual(cat_ov.ivs.count(), 0)
        self.assertEqual(cat_fb20.ivs.count(), 0)
        self.assertEqual(cat_fb20_ov.ivs.count(), 0)
        self.assertEqual(cat_fb20_g.ivs.count(), 2)

        self._get_veranst_or_fail(typ='vu', name='Grundlagen der Informatik I', cat=cat_fb20_g)
        self._get_veranst_or_fail(typ='vu', name='Grundlagen der Informatik II', cat=cat_fb20_g)

    def test_parse_vv_xml(self):
        self._parse_vv_xml('vv_test.xml')

    def test_parse_vv_xml_nbsp(self):
        self._parse_vv_xml('vv_test_nbsp.xml')
