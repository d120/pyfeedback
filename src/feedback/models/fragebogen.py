# coding=utf-8

from django.db import models


class Fragebogen(models.Model):
    FACH_CHOICES = (
        ('inf', 'Informatik'),
        ('math', 'Mathematik'),
        ('ce', 'Computational Engineering'),
        ('ist', 'Informationssystemtechnik'),
        ('etit', 'Elektrotechnik'),
        ('psyit', 'Psychologie in IT'),
        ('winf', 'Wirtschaftsinformatik'),
        ('sonst', 'etwas anderes'),
    )

    ABSCHLUSS_CHOICES = (
        ('bsc', 'Bachelor'),
        ('msc', 'Master'),
        ('dipl', 'Diplom'),
        ('lehr', 'Lehramt'),
        ('sonst', 'anderer Abschluss'),
    )

    GESCHWINDIGKEIT_CHOICES = (
        ('s', 'zu schnell'),
        ('l', 'zu langsam'),
    )

    NIVEAU_CHOICES = (
        ('h', 'zu hoch'),
        ('n', 'zu niedrig'),
    )

    BOOLEAN_CHOICES = (
        ('j', 'ja'),
        ('n', 'nein'),
    )

    SEMESTER_CHOICES = (
        ('1-2', '1-2'),
        ('3-4', '3-4'),
        ('5-6', '5-6'),
        ('>=7', '>=7'),
    )

    SEMESTER_CHOICES16 = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '>=10'),
    )
    GESCHLECHT_CHOICES = (
        ('w', 'weiblich'),
        ('m', 'männlich'),
        ('s', 'sonstiges'),
    )

    STUDIENBERECHTIGUNG_CHOICES = (
        ('d', 'Deutschland'),
        ('o', 'anderes Land'),
    )

    VERANSTALTUNG_GEHOERT = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '<=4'),
    )

    KLAUSUR_ANGETRETEN = (
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
    )

    STUNDEN_NACHBEARBEITUNG = (
        ('0', '0'),
        ('1', '0.5'),
        ('2', '1'),
        ('3', '2'),
        ('4', '3'),
        ('5', '4'),
        ('6', '5'),
        ('7', '>=5')

    )

    veranstaltung = models.ForeignKey('feedback.Veranstaltung')

    def __unicode__(self):
        return u'Fragebogen zu "%s" (%s, %s)' % (self.veranstaltung.name,
                                                 self.veranstaltung.get_typ_display(),
                                                 self.veranstaltung.semester.short())

    class Meta:
        abstract = True
        app_label = 'feedback'

class Ergebnis(models.Model):
    #TODO: durch OneToOneField ersetzen
    veranstaltung = models.OneToOneField('feedback.Veranstaltung')
    anzahl = models.PositiveIntegerField()
    parts = []
    hidden_parts = []
    parts_vl = []
    parts_ue = []

    def values(self):
        """Ergebnisse pro Veranstaltung in Liste zusammenfassen"""

        # Sonderbehandlung für Vorlesungen ohne Übung: Übungsergebnisse entfernen
        if self.veranstaltung.typ == 'v':
            return self._do_get_values(self.parts_vl) + [[None, 0]] * len(self.parts_ue)

        return self._do_get_values(self.parts)

    def all_values(self):
        """auch versteckte Ergebnisse pro Veranstaltung in Liste zusammenfassen"""

        return self.values() + self._do_get_values(self.hidden_parts)

    def _do_get_values(self, parts):
        values = []
        for part in parts:
            val = getattr(self, part[0])
            count = getattr(self, part[0]+'_count')
            values.append([val, count])

        return values

    def __unicode__(self):
        return u'Ergebnisse zu "%s" (%s, %s)' % (self.veranstaltung.name, self.veranstaltung.get_typ_display(), self.veranstaltung.semester)

    class Meta:
        abstract = True
        app_label = 'feedback'

class Kommentar(models.Model):
    veranstaltung = models.OneToOneField('feedback.Veranstaltung')
    autor = models.ForeignKey('feedback.Person')
    text = models.TextField()

    class Meta:
        verbose_name = 'Kommentar'
        verbose_name_plural = 'Kommentare'
        app_label = 'feedback'

    def semester(self):
        return self.veranstaltung.semester

    def typ(self):
        return self.veranstaltung.get_typ_display()

    def name(self):
        return self.veranstaltung.name

    def __unicode__(self):
        return 'Kommentar zu "%s" (%s, %s)' % (self.name(), self.typ(), self.semester())
