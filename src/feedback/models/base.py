# coding=utf-8

from __future__ import unicode_literals

import random

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.utils import OperationalError
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from feedback.tools import ean_checksum_calc, ean_checksum_valid

from django.utils import formats

import datetime


class Semester(models.Model):
    FRAGEBOGEN_CHOICES = (
        ('2008', 'Fragebogen 2008'),
        ('2009', 'Fragebogen 2009'),
        ('2012', 'Fragebogen 2012'),
        ('2016', 'Fragebogen 2016'),

    )
    SICHTBARKEIT_CHOICES = (
        ('ADM', u'Administratoren'),
        ('VER', u'Veranstalter'),
        ('ALL', u'alle (öffentlich)'),
    )

    semester = models.IntegerField(help_text=u'Aufbau: YYYYS, wobei YYYY = Jahreszahl und S = Semester (0=SS, 5=WS).',
                                   unique=True)
    fragebogen = models.CharField(max_length=5, choices=FRAGEBOGEN_CHOICES,
                                  help_text=u'Verwendete Version des Fragebogens.')
    sichtbarkeit = models.CharField(max_length=3, choices=SICHTBARKEIT_CHOICES,
                                    help_text=u'Sichtbarkeit der Evaluationsergebnisse.<br /><em>' +
                                              SICHTBARKEIT_CHOICES[0][1] +
                                              u':</em> nur für Mitglieder des Feedback-Teams<br /><em>' +
                                              SICHTBARKEIT_CHOICES[1][1] +
                                              u':</em> Veranstalter und Mitglieder des Feedback-Teams<br /><em>' +
                                              SICHTBARKEIT_CHOICES[2][1] +
                                              u':</em> alle (beschränkt auf das Uninetz)<br />'
                                    )
    vollerhebung = models.BooleanField(default=False)

    def _format_generic(self, ss, ws, space, modulus):
        sem = self.semester // 10
        if (modulus > 0):
            sem = sem % modulus

        if self.semester % 10 == 0:
            return u'%s%s%d' % (ss, space, sem)
        else:
            return u'%s%s%d/%d' % (ws, space, sem, sem + 1)

    def _format(self, ss, ws):
        return self._format_generic(ss, ws, ' ', 0)

    def short(self):
        return self._format('SS', 'WS')

    def long(self):
        return self._format('Sommersemester', 'Wintersemester')

    def evasys(self):
        return self._format_generic('SS', 'WS', '', 100)

    def last_Auswertungstermin(self):
        """Letzter Tag der als Auswertungstermin angegeben werden kann"""
        year = 0
        moth = 0
        day = 15
        # Sommersemester
        if self.semester % 10 == 0:
            year = self.semester / 10
            month = 10
        # Wintersemester
        else:
            year = (self.semester / 10) + 1
            month = 4

        return datetime.datetime(year, month, day)

    def last_Auswertungstermin_to_late_human(self):
        """Der erste Tag der nach dem letzten Auswertungstermin liegt formatiert"""
        toLateDate = self.last_Auswertungstermin() + datetime.timedelta(days=1)
        return formats.date_format(toLateDate, 'DATE_FORMAT')

    def auswertungstermin_years(self):
        """Die Jahre in denen der Auswertungstermin liegen kann"""
        return self.last_Auswertungstermin().year,

    def __unicode__(self):
        return self.long()

    class Meta:
        verbose_name = 'Semester'
        verbose_name_plural = 'Semester'
        ordering = ['-semester']
        app_label = 'feedback'

    @staticmethod
    def current():
        try:
            return Semester.objects.order_by('-semester')[0]
        except IndexError:
            return None
        except OperationalError:
            return None


class Person(models.Model):
    GESCHLECHT_CHOICES = (
        ('', ''),
        ('m', 'Herr'),
        ('w', 'Frau'),
    )

    GESCHLECHT_EVASYS_XML = {
        '': '',
        'm': 'm',
        'w': 'f',
    }

    geschlecht = models.CharField(max_length=1, choices=GESCHLECHT_CHOICES, blank=True, verbose_name=u'Anrede')
    vorname = models.CharField(_('first name'), max_length=30, blank=True)
    nachname = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('e-mail address'), blank=True)
    anschrift = models.CharField(_('anschrift'), max_length=80, blank=True,
                                 help_text='Bitte geben sie die Anschrift so an, dass der Versand per Hauspost problemlos erfolgen kann.')
    fachgebiet = models.CharField(_('Fachgebiet'), max_length=80, blank=True)

    def full_name(self):
        return u'%s %s' % (self.vorname, self.nachname)

    def get_evasys_key(self):
        return "pe-%s" % self.id

    def get_evasys_geschlecht(self):
        return Person.GESCHLECHT_EVASYS_XML[self.geschlecht]

    def __unicode__(self):
        return u'%s, %s' % (self.nachname, self.vorname)

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'Personen'
        ordering = 'nachname', 'vorname'
        app_label = 'feedback'

    @staticmethod
    def create_from_import_person(ip):
        # Prüfen, ob Benutzer existiert
        try:
            return Person.objects.filter(vorname=ip.vorname, nachname=ip.nachname)[0]
        except (Person.DoesNotExist, IndexError):
            try:
                return AlternativVorname.objects.filter(vorname=ip.vorname).get().person
            except (AlternativVorname.DoesNotExist, IndexError):
                return Person.objects.create(vorname=ip.vorname, nachname=ip.nachname)

    @staticmethod
    def persons_to_edit(semester=None):
        if semester is None:
            semester = Semester.current()
        return Person.objects.filter(Q(geschlecht='') | Q(email=''), veranstaltung__semester=semester)\
            .order_by('id').distinct()

    @staticmethod
    def all_edited_persons():
        return Person.objects.filter(~Q(geschlecht='') & ~Q(email='')).order_by('id').distinct()

    @staticmethod
    def persons_with_similar_names(vorname, nachname):
        return Person.all_edited_persons().filter(vorname__startswith=vorname, nachname=nachname)

    @staticmethod
    def veranstaltungen(person):
        return Veranstaltung.objects.filter(veranstalter=person)

    @staticmethod
    def replace_veranstalter(new, old):
        veranstaltungen = Person.veranstaltungen(new)

        # replace every lecture held by 'new' with 'old'
        for v in veranstaltungen:
            v.veranstalter = [old]
            v.save()

        # save the second name from 'new' as the alternative first name of 'old'
        av = AlternativVorname.objects.create(vorname=new.vorname, person=old)
        av.save()

    @staticmethod
    def is_veranstalter(person):
        return Person.veranstaltungen(person).count() > 0


class AlternativVorname(models.Model):
    vorname = models.CharField(_('first name'), max_length=30, blank=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    @staticmethod
    def persons_to_edit(semester=None):
        if semester is None:
            semester = Semester.current()
        return Person.objects.filter(Q(geschlecht='') | Q(email=''), veranstaltung__semester=semester)\
            .order_by('id').distinct()


class Veranstaltung(models.Model):
    TYP_CHOICES = (
        ('v', 'Vorlesung'),
        ('vu', 'Vorlesung mit Übung'),
        ('pr', 'Praktikum'),
        ('se', 'Seminar'),
    )
    SPRACHE_CHOICES = (
        ('de', 'Deutsch'),
        ('en', 'Englisch'),
    )
    # 0    undefiniert
    # 1    Vorlesung
    # 2    Seminar
    # 3    Proseminar
    # 4    Übung
    # 5    Praktikum
    # 6    Tutorium
    # 7    Sonstige
    # 8    Projekt
    # 9    Vorlesung + Übung
    # 10    Ringvorlesung
    # 11    Vorlesung+Praktikum
    VORLESUNGSTYP = {
        'v': 1,
        'vu': 9,
        'pr': 5,
        'se': 2,
    }

    VORLESUNGSTYP_XML = {
        'v': 'Vorlesung',
        'vu': 'Vorlesung + Übung',
        'pr': 'Praktikum',
        'se': 'Seminar',
    }

    # Bögen 2015

    ## Deutsch
    # PD FB20Pv1 2677
    # SD FB20Sv2 2681
    # ÜD FB20Üv1 2675
    # VD FB20Vv1 2679

    ## Englisch
    # PE FB20Pv1e 2704
    # SE FB20Sv1e 2702
    # ÜE FB20Üv1e 2700
    # VE FB20Vv1e 2698

    EVASYS_BOGENKENNUNG_DE = {
        'pr': 'FB20Pv1',
        'se': 'FB20Sv2',
        'u': 'FB20Üv1',
        'v': 'FB20Vv1',
        'vu': 'FB20Vv1',  # FIXME: Eigentlich zwei Umfragen
    }

    EVASYS_BOGENKENNUNG_EN = {
        'pr': 'FB20Pv1e',
        'se': 'FB20Sv1e',
        'u': 'FB20Üv1e',
        'v': 'FB20Vv1e',
        'vu': 'FB20Vv1e',  # FIXME: Eigentlich zwei Umfragen
    }

    BARCODE_BASE = 2 * 10 ** 11

    # Helfertext für Dozenten für den Veranstaltungstyp.
    vlNoEx = 'Wenn Ihre Vorlesung keine Übung hat wählen Sie bitte <i>%s</i> aus'
    for cur in TYP_CHOICES:
        if cur[0] == 'v':
            vlNoEx = vlNoEx % cur[1]
            break

    typ = models.CharField(max_length=2, choices=TYP_CHOICES, help_text=vlNoEx)
    name = models.CharField(max_length=150)
    semester = models.ForeignKey(Semester)
    lv_nr = models.CharField(max_length=15, blank=True, verbose_name=u'LV-Nummer')
    grundstudium = models.BooleanField()
    evaluieren = models.BooleanField()
    veranstalter = models.ManyToManyField(Person, blank=True,
                                          help_text=u'Alle Personen, die mit der Veranstaltung befasst sind und z.B. Fragebögen bestellen können sollen.')

    sprache = models.CharField(max_length=2, choices=SPRACHE_CHOICES, null=True, blank=True)
    anzahl = models.IntegerField(null=True, blank=True)
    verantwortlich = models.ForeignKey(Person, related_name='verantwortlich', null=True, blank=True,
                                       help_text=u'Diese Person wird von uns bei Rückfragen kontaktiert und bekommt die Fragenbögen zugeschickt')
    ergebnis_empfaenger = models.ManyToManyField(Person, blank=True,
                                                 related_name='ergebnis_empfaenger',
                                                 verbose_name=u'Empfänger der Ergebnisse',
                                                 help_text=u'An diese Personen werden die Ergebnisse per E-Mail geschickt.')
    auswertungstermin = models.DateField(null=True, blank=True,
                                         verbose_name=u'Auswertungstermin',
                                         help_text=u'An welchem Tag sollen Fragebögen für diese Veranstaltung ausgewerter werden? ' +
                                                   u'Fragebögen die danach eintreffen werden nicht mehr ausgewertet.')
    bestelldatum = models.DateField(null=True, blank=True)
    access_token = models.CharField(max_length=16, blank=True)
    freiefrage1 = models.TextField(verbose_name='1. Freie Frage', blank=True)
    freiefrage2 = models.TextField(verbose_name='2. Freie Frage', blank=True)
    kleingruppen = models.TextField(verbose_name='Kleingruppen', blank=True)

    def get_evasys_typ(self):
        return Veranstaltung.VORLESUNGSTYP[self.typ]

    def get_evasys_typ_xml(self):
        return Veranstaltung.VORLESUNGSTYP_XML[self.typ]

    def get_evasys_key(self):
        return 'lv-%s' % self.id

    def get_evasys_kennung(self):
        return "%s-%s" % (self.lv_nr, self.semester.evasys())

    def get_evasys_survery_key(self):
        return 'su-%s' % self.id

    def get_evasys_survery_key_uebung(self):
        return 'su-%s-u' % self.id

    # FIXME: bogen name sollte nicht statisch sein!
    def get_evasys_bogen(self):
        if self.sprache == 'de':
            return Veranstaltung.EVASYS_BOGENKENNUNG_DE[self.typ]
        elif self.sprache == 'en':
            return Veranstaltung.EVASYS_BOGENKENNUNG_EN[self.typ]
        else:
            return ''

    def get_evasys_bogen_uebung(self):
        """Kennung für den Übungsfragebogen"""
        if self.typ == 'vu':
            if self.sprache == 'de':
                return Veranstaltung.EVASYS_BOGENKENNUNG_DE['u']
            elif self.sprache == 'en':
                return Veranstaltung.EVASYS_BOGENKENNUNG_EN['u']

        return ''

    def get_evasys_umfragetyp(self):
        """Deckblatt oder Selbstdruck verfahren"""
        result = 'coversheet'  # Deckblatt verfahren
        if self.typ in ('se', 'pr'):
            result = 'hardcopy'  # Selbstdruck verfahren
        return result

    def get_barcode_number(self, tutorgruppe=0):
        """Barcode Nummer für diese Veranstaltung"""
        if tutorgruppe > 99:
            raise ValueError("Tutorgruppe muss kleiner 100 sein")

        if isinstance(tutorgruppe, int) == False:
            raise ValueError("Tutorgruppe muss eine ganze Zahl sein")

        base = Veranstaltung.BARCODE_BASE
        veranst = self.pk
        code_draft = base + (veranst * 100) + tutorgruppe
        checksum = ean_checksum_calc(code_draft)

        code = (code_draft * 10) + checksum

        return code

    @staticmethod
    def decode_barcode(barcode):
        if (ean_checksum_valid(barcode) != True):
            raise ValueError("Der Barcode ist nicht valide")

        # entferne das Padding am Anfang
        information = barcode % Veranstaltung.BARCODE_BASE

        # entferne die checksumme
        information = information // 10

        # die letzten zwei Stellen sind die Uebungsgruppe
        tutorgroup = information % 100

        # Alle Stellen vor der Uebungsgruppe sind der PK der Veranstaltung
        veranstaltung = information // 100

        return {'veranstaltung': veranstaltung, 'tutorgroup': tutorgroup}

    def __unicode__(self):
        return u"%s [%s] (%s)" % (self.name, self.typ, self.semester.short())

    def auwertungstermin_to_late_msg(self):
        toLateDate = self.semester.last_Auswertungstermin_to_late_human()
        return 'Der Auswertungstermin muss vor dem %s liegen.' % toLateDate

    def has_uebung(self):
        """Gibt True zurück wenn die Veranstaltung eine Übung hat sonst False"""
        result = False
        if self.typ == 'vu':
            result = True
        return result

    def veranstalter_list(self):
        """Eine Liste aller Veranstalter dieser Veranstaltung"""
        list = map(lambda x: x.full_name(), self.veranstalter.all())
        return ', '.join(list)

    def clean(self, *args, **kwargs):
        super(Veranstaltung, self).clean(*args, **kwargs)

        if self.auswertungstermin != None and self.auswertungstermin > self.semester.last_Auswertungstermin().date():
            raise ValidationError(self.auwertungstermin_to_late_msg())

    def save(self, *args, **kwargs):
        # beim Speichern Zugangsschlüssel erzeugen, falls noch keiner existiert
        if not self.access_token:
            self.access_token = '%016x' % random.randint(0, 16 ** 16 - 1)
        super(Veranstaltung, self).save(*args, **kwargs)

    def link_veranstalter(self):  # @see http://stackoverflow.com/a/17948593
        """Gibt die URL für die Bestellunng durch den Veranstalter zurück"""
        link_veranstalter = 'https://www.fachschaft.informatik.tu-darmstadt.de%s' % reverse('veranstalter-login')
        link_suffix_format = '?vid=%d&token=%s'
        if self.pk is not None and self.access_token is not None:
            return link_veranstalter + (link_suffix_format % (self.pk, self.access_token))
        else:
            return "Der Veranstalter Link wird erst nach dem Anlegen angezeigt"

    def csv_to_tutor(self):
        """Erzeuge Tutoren Objekte aus der CSV Eingabe der Veranstalter"""
        input_clean = self.kleingruppen.strip()
        input_lines = input_clean.splitlines()
        nummer = 1
        for l in input_lines:
            # skip empty lines
            if len(l.strip()) > 1:
                row = l.split(',', 3)
                # skip lines which are not well formated
                if len(row) > 1:
                    row = [x.strip() for x in row]
                    anmerkungInput = ''
                    if len(row) > 3:
                        anmerkungInput = row[3]

                    Tutor.objects.get_or_create(
                        veranstaltung=self,
                        nummer=nummer,
                        nachname=row[0],
                        vorname=row[1],
                        email=row[2],
                        anmerkung=anmerkungInput,
                    )

                    nummer += 1

    class Meta:
        verbose_name = 'Veranstaltung'
        verbose_name_plural = 'Veranstaltungen'
        ordering = ['semester', 'typ', 'name']
        unique_together = ('name', 'lv_nr', 'semester')
        app_label = 'feedback'


class Tutor(models.Model):
    """Ein Tutor der eine Übung einer Lehrveranstaltung hält"""
    nummer = models.PositiveSmallIntegerField()
    vorname = models.CharField(_('first name'), max_length=30)
    nachname = models.CharField(_('last name'), max_length=30)
    email = models.EmailField(_('e-mail address'))
    anmerkung = models.CharField(max_length=100)
    veranstaltung = models.ForeignKey(Veranstaltung)

    def get_barcode_number(self):
        return self.veranstaltung.get_barcode_number(tutorgruppe=self.nummer)

    def __unicode__(self):
        return u'%s %s %d' % (self.vorname, self.nachname, self.nummer)

    class Meta:
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutoren'
        unique_together = (('nummer', 'veranstaltung'),)
        app_label = 'feedback'


class Einstellung(models.Model):
    name = models.CharField(max_length=100, unique=True)
    wert = models.CharField(max_length=255, blank=True)

    @staticmethod
    def get(name):
        return Einstellung.objects.get(name=name).wert

    class Meta:
        verbose_name = 'Einstellung'
        verbose_name_plural = 'Einstellungen'
        app_label = 'feedback'

    def __unicode__(self):
        return u'%s = "%s"' % (self.name, self.wert)


class Mailvorlage(models.Model):
    subject = models.CharField(max_length=100, unique=True)
    body = models.TextField()

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = 'Mailvorlage'
        verbose_name_plural = verbose_name + 'n'
        ordering = ['subject']
        app_label = 'feedback'


class BarcodeScanner(models.Model):
    """Ein Barcode Scanner der fuer das Scannen von Barcodes benutzt wird"""
    token = models.CharField(max_length=64)
    description = models.TextField()

    def __unicode__(self):
        return self.description

    class Meta:
        verbose_name = 'Barcode Scanner'
        verbose_name_plural = 'Barcode Scanner'
        app_label = 'feedback'


class BarcodeScannEvent(models.Model):
    """Stell den Scann eines Barcodes dar"""
    veranstaltung = models.ForeignKey(Veranstaltung)
    scanner = models.ForeignKey(BarcodeScanner)
    tutorgroup = models.ForeignKey(Tutor, null=True, blank=True)
    barcode = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'BarcodeScannEvent'
        verbose_name_plural = 'BarcodeScannEvents'
        app_label = 'feedback'

    def save(self, *args, **kwargs):
        """Extrahiere die Veranstaltungsdaten aus dem Barcode
        teil zwei zum ModelForm"""
        barcode_decode = Veranstaltung.decode_barcode(self.barcode)
        verst_obj = Veranstaltung.objects.get(pk=barcode_decode['veranstaltung'])
        self.veranstaltung = verst_obj

        if (barcode_decode['tutorgroup'] >= 1):
            tutorgroup = Tutor.objects.get(veranstaltung=verst_obj, nummer=barcode_decode['tutorgroup'])
            self.tutorgroup = tutorgroup

        super(BarcodeScannEvent, self).save(*args, **kwargs)
