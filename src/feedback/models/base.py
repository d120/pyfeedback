# coding=utf-8


import random

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.utils import OperationalError
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q

from feedback.tools import ean_checksum_calc, ean_checksum_valid
from django.contrib.auth.models import User

from django.utils import formats

import datetime


class Semester(models.Model):
    """Repräsentiert ein Semester der TUD."""
    FRAGEBOGEN_CHOICES = (
        ('2008', 'Fragebogen 2008'),
        ('2009', 'Fragebogen 2009'),
        ('2012', 'Fragebogen 2012'),
        ('2016', 'Fragebogen 2016'),
        ('2020', 'Fragebogen 2020'),

    )
    SICHTBARKEIT_CHOICES = (
        ('ADM', _('Administratoren')),
        ('VER', _('Veranstalter')),
        ('ALL', _('alle (öffentlich)')),
    )

    semester = models.IntegerField(help_text='Aufbau: YYYYS, wobei YYYY = Jahreszahl und S = Semester (0=SS, 5=WS).',
                                   unique=True)
    fragebogen = models.CharField(max_length=5, choices=FRAGEBOGEN_CHOICES,
                                  help_text=_('Verwendete Version des Fragebogens.'))
    sichtbarkeit = models.CharField(max_length=3, choices=SICHTBARKEIT_CHOICES,
                                    help_text='Sichtbarkeit der Evaluationsergebnisse.<br /><em>' +
                                              SICHTBARKEIT_CHOICES[0][1] +
                                              ':</em> nur für Mitglieder des Feedback-Teams<br /><em>' +
                                              SICHTBARKEIT_CHOICES[1][1] +
                                              ':</em> Veranstalter und Mitglieder des Feedback-Teams<br /><em>' +
                                              SICHTBARKEIT_CHOICES[2][1] +
                                              ':</em> alle (beschränkt auf das Uninetz)<br />'
                                    )
    vollerhebung = models.BooleanField(default=False)
    standard_ergebnisversand = models.DateField(null=True, blank=True, verbose_name=_('Ergebnisversand'), help_text=_('Standarddatum für den Ergebnisversand'))

    def _format_generic(self, ss, ws, space, modulus):
        sem = self.semester // 10
        if (modulus > 0):
            sem = sem % modulus

        if self.semester % 10 == 0:
            return '%s%s%d' % (ss, space, sem)
        else:
            return '%s%s%d/%d' % (ws, space, sem, sem + 1)

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
        month = 0
        day = 15
        # Sommersemester
        if self.semester % 10 == 0:
            year = self.semester / 10
            month = 10
        # Wintersemester
        else:
            year = (self.semester / 10) + 1
            month = 4

        return datetime.datetime(int(year), int(month), int(day))

    def last_Auswertungstermin_to_late_human(self):
        """Der erste Tag der nach dem letzten Auswertungstermin liegt formatiert"""
        toLateDate = self.last_Auswertungstermin() + datetime.timedelta(days=1)
        return formats.date_format(toLateDate, 'DATE_FORMAT')

    def auswertungstermin_years(self):
        """Die Jahre in denen der Auswertungstermin liegen kann"""
        return self.last_Auswertungstermin().year,

    def __str__(self):
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


class Fachgebiet(models.Model):
    """Repräsentiert ein Fachgebiet für das FB20"""
    name = models.CharField(max_length=80)
    kuerzel = models.CharField(max_length=10)

    @staticmethod
    def get_fachgebiet_from_email(email):
        """
        Gibt ein Fachgebiet anhand einer E-Mail Adresse zurück
        :param email: E-Mail String
        :return: Fachgebiet
        """
        try:
            suffix = email.split('@')[-1]
            return EmailEndung.objects.get(domain=suffix).fachgebiet
        except Exception:
            return None

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Fachgebiet')
        verbose_name_plural = _('Fachgebiete')
        app_label = 'feedback'


class EmailEndung(models.Model):
    """Repräsentiert alle Domains die für E-Mails von Veranstaltern verwendet werden"""
    fachgebiet = models.ForeignKey(Fachgebiet,
                                   blank=True,
                                   verbose_name=_("Fachgebiet"),
                                   help_text=_("Hier soll der Domainname einer Email-Adresse eines Fachgebiets stehen."),
                                   on_delete=models.CASCADE)
    domain = models.CharField(max_length=150,
                              null=True)

    def __str__(self):
        return self.domain

    class Meta:
        verbose_name = _('Fachgebiet Emailendung')
        verbose_name_plural = _('Fachgebiet Emailendungen')
        app_label = 'feedback'


class FachgebietEmail(models.Model):
    """Repräsentiert die E-Mail Domänen für die jeweiligen Fachgebiete des FBs 20."""
    fachgebiet = models.ForeignKey(Fachgebiet, related_name='fachgebiet', verbose_name=_("Fachgebiet"), on_delete=models.CASCADE)
    email_sekretaerin = models.EmailField(blank=True)

    class Meta:
        verbose_name = _('Fachgebiet Email')
        verbose_name_plural = _('Fachgebiet Emails')
        app_label = 'feedback'


class Person(models.Model):
    """Repräsentiert eine Person der TUD aus dem FB20."""
    GESCHLECHT_CHOICES = (
        ('', ''),
        ('m', _('Herr')),
        ('w', _('Frau')),
    )

    GESCHLECHT_EVASYS_XML = {
        '': '',
        'm': 'm',
        'w': 'f',
    }

    geschlecht = models.CharField(max_length=1, choices=GESCHLECHT_CHOICES, blank=True, verbose_name='Anrede')
    vorname = models.CharField(_('first name'), max_length=30, blank=True)
    nachname = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('E-Mail'), blank=True)
    anschrift = models.CharField(_('anschrift'), max_length=80, blank=True,
                                 help_text=_('Tragen Sie bitte nur die Anschrift ohne Namen ein, '
                                           'da der Name automatisch hinzugefügt wird.'))
    fachgebiet = models.ForeignKey(Fachgebiet, null=True, blank=True, on_delete=models.CASCADE)

    def full_name(self):
        return '%s %s' % (self.vorname, self.nachname)

    def get_evasys_key(self):
        return "pe-%s" % self.id

    def get_evasys_geschlecht(self):
        return Person.GESCHLECHT_EVASYS_XML[self.geschlecht]

    def __str__(self):
        return '%s, %s' % (self.nachname, self.vorname)

    def printable(self) -> bool:
        """ Check whether the user has all required fields for printing (e.g. for generating the stickers)
        """
        return self.vorname != "" and self.nachname != "" and self.email != "" and self.anschrift != ""

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Personen')
        ordering = 'nachname', 'vorname'
        app_label = 'feedback'

    @staticmethod
    def create_from_import_person(ip):
        """
        Erstellt Personen aus dem Import
        :param ip: die importierte Person
        :return: Person
        """
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
        """
        Gibt die Personen zurück, die noch bearbeitet werden müssen.
        :param semester: bei None, das aktuelle Semester, ansonsten das Angegebene.
        :return: Person
        """
        if semester is None:
            semester = Semester.current()
        return Person.objects.filter(Q(geschlecht='') | Q(email=''), veranstaltung__semester=semester)\
            .order_by('id').distinct()

    @staticmethod
    def all_edited_persons():
        """
        Gibt alle Personen zurück, die schon bearbeitet wurden.
        :return: Person
        """
        return Person.objects.filter(~Q(geschlecht='') & ~Q(email='')).order_by('id').distinct()

    @staticmethod
    def persons_with_similar_names(vorname, nachname):
        """
        Gibt alle Personen zurück, die sich im Namen ähneln.
        :param vorname: String
        :param nachname: String
        :return: Person
        """
        return Person.all_edited_persons().filter(vorname__startswith=vorname, nachname=nachname)

    @staticmethod
    def veranstaltungen(person):
        """
        Gibt die Veranstaltungen einer Person zurück.
        :param person: Person
        :return: Veranstaltung
        """
        return Veranstaltung.objects.filter(veranstalter=person)

    @staticmethod
    def replace_veranstalter(new, old):
        """
        Ersetzt einen "alten" Veranstalter durch einen "neuen".
        Zum Beispiel wenn Dozenten sich beim Namen ähneln und dementsprechend identisch sind.
        Wenn dies der Fall ist, wird ersetzt und ein AlternativVorname erzeugt, der sich die ähnlichen Namen merkt.
        :param new: die neue Person
        :param old: die alte Person
        """
        veranstaltungen = Person.veranstaltungen(new)

        # replace every lecture held by 'new' with 'old'
        for v in veranstaltungen:
            v.veranstalter.set([old])
            v.save()

        # save the second name from 'new' as the alternative first name of 'old'
        av = AlternativVorname.objects.create(vorname=new.vorname, person=old)
        av.save()

    @staticmethod
    def is_veranstalter(person):
        """
        prüft, ob eine Person ein Veranstalter ist.
        :param person: Person
        :return: True, wenn Veranstalter, ansonsten False
        """
        return Person.veranstaltungen(person).count() > 0


class AlternativVorname(models.Model):
    """Repräsentiert einen alternativen Vornamen für eine Person."""
    vorname = models.CharField(_('first name'), max_length=30, blank=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class Veranstaltung(models.Model):
    """Repräsentiert eine Veranstaltung der TUD."""
    TYP_CHOICES = (
        ('v', _('Vorlesung')),
        ('vu', _('Vorlesung mit Übung')),
        ('pr', _('Praktikum')),
        ('se', _('Seminar')),
    )

    SPRACHE_CHOICES = (
        ('de', _('Deutsch')),
        ('en', _('Englisch')),
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

    # Deutsch
    # PD FB20Pv1 2677
    # SD FB20Sv2 2681
    # ÜD FB20Üv1 2675
    # VD FB20Vv1 2679

    # Englisch
    # PE FB20Pv1e 2704
    # SE FB20Sv1e 2702
    # ÜE FB20Üv1e 2700
    # VE FB20Vv1e 2698

    EVASYS_BOGENKENNUNG_DE = {
        'pr': 'FB20Prd1',
        'se': 'FB20Sed1',
        'u': 'FB20Ud1',
        'v': 'FB20VLd2',
        'vu': 'FB20VLd2',
    }

    EVASYS_BOGENKENNUNG_EN = {
        'pr': 'FB20Prd1',
        'se': 'FB20Sed1',
        'u': 'FB20Ud1',
        'v': 'FB20VLd2',
        'vu': 'FB20VLd2',
    }

    BARCODE_BASE = 2 * 10 ** 11

    # Vorlesungsstatus
    STATUS_ANGELEGT = 100
    STATUS_BESTELLUNG_GEOEFFNET = 200
    STATUS_KEINE_EVALUATION = 300
    STATUS_KEINE_EVALUATION_FINAL = 310
    STATUS_BESTELLUNG_LIEGT_VOR = 500
    STATUS_BESTELLUNG_WIRD_VERARBEITET = 510
    STATUS_GEDRUCKT = 600
    STATUS_VERSANDT = 700
    STATUS_BOEGEN_EINGEGANGEN = 800
    STATUS_BOEGEN_GESCANNT = 900
    STATUS_ERGEBNISSE_VERSANDT = 1000

    STATUS_CHOICES = (
        (STATUS_ANGELEGT, _('Angelegt')),
        (STATUS_BESTELLUNG_GEOEFFNET, _('Bestellung geöffnet')),
        (STATUS_KEINE_EVALUATION, _('Keine Evaluation')),
        (STATUS_KEINE_EVALUATION_FINAL, _('Keine Evaluation final')),
        (STATUS_BESTELLUNG_LIEGT_VOR, _('Bestellung liegt vor')),
        (STATUS_BESTELLUNG_WIRD_VERARBEITET, _('Bestellung wird verarbeitet')),
        (STATUS_GEDRUCKT, _('Gedruckt')),
        (STATUS_VERSANDT, _('Versandt')),
        (STATUS_BOEGEN_EINGEGANGEN, _('Bögen eingegangen')),
        (STATUS_BOEGEN_GESCANNT, _('Bögen gescannt')),
        (STATUS_ERGEBNISSE_VERSANDT, _('Ergebnisse versandt')),
    )

    BOOL_CHOICES = (
        (True, _('Ja')),
        (False, _('Nein')),
    )

    # TODO: not the final version of status transition
    STATUS_UEBERGANG = {
        STATUS_ANGELEGT: (STATUS_GEDRUCKT, STATUS_BESTELLUNG_GEOEFFNET),
        STATUS_BESTELLUNG_GEOEFFNET: (STATUS_KEINE_EVALUATION, STATUS_BESTELLUNG_LIEGT_VOR),
        STATUS_KEINE_EVALUATION: (STATUS_BESTELLUNG_LIEGT_VOR,),
        STATUS_BESTELLUNG_WIRD_VERARBEITET: (STATUS_GEDRUCKT,),
        STATUS_BESTELLUNG_LIEGT_VOR: (STATUS_GEDRUCKT, STATUS_BESTELLUNG_LIEGT_VOR, STATUS_KEINE_EVALUATION),
        STATUS_GEDRUCKT: (STATUS_VERSANDT,),
        STATUS_VERSANDT: (STATUS_BOEGEN_EINGEGANGEN,),
        STATUS_BOEGEN_EINGEGANGEN: (STATUS_BOEGEN_GESCANNT,),
        STATUS_BOEGEN_GESCANNT: (STATUS_ERGEBNISSE_VERSANDT,)
    }

    DIGITALE_EVAL = [
        ('T', 'TANs'),
        ('L', 'Losung'),
    ]

    MIN_BESTELLUNG_ANZAHL = 5

    # Helfertext für Dozenten für den Veranstaltungstyp.
    vlNoEx = _('Wenn Ihre Vorlesung keine Übung hat wählen Sie bitte <i>%s</i> aus')
    for cur in TYP_CHOICES:
        if cur[0] == 'v':
            vlNoEx = vlNoEx % cur[1]
            break

    typ = models.CharField(verbose_name=_("Typ"), max_length=2, choices=TYP_CHOICES, help_text=vlNoEx)
    name = models.CharField(verbose_name=_("Name"),max_length=150)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    lv_nr = models.CharField(max_length=15, blank=True, verbose_name=_('LV-Nummer'))
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_ANGELEGT)
    grundstudium = models.BooleanField(verbose_name=_("Grundstudium"))
    evaluieren = models.BooleanField(verbose_name=_("Evaluieren"), choices=BOOL_CHOICES, default=True)
    veranstalter = models.ManyToManyField(Person, verbose_name=_("Veranstalter"), blank=True,
                                          help_text=_('Alle Personen, die mit der Veranstaltung befasst sind und z.B. Fragebögen bestellen können sollen.'))

    sprache = models.CharField(max_length=2, choices=SPRACHE_CHOICES, null=True, blank=True, verbose_name=_("Sprache"))
    anzahl = models.IntegerField(verbose_name=_("Anzahl"), null=True, blank=True)
    verantwortlich = models.ForeignKey(Person, related_name='verantwortlich', verbose_name=_("Verantwortlich"), null=True, blank=True, on_delete=models.CASCADE,
                                       help_text=_('Diese Person wird von uns bei Rückfragen kontaktiert und bekommt die Fragenbögen zugeschickt'))
    ergebnis_empfaenger = models.ManyToManyField(Person, blank=True,
                                                 related_name='ergebnis_empfaenger',
                                                 verbose_name=_('Empfänger der Ergebnisse'),
                                                 help_text=_('An diese Personen werden die Ergebnisse per E-Mail geschickt.'))
    primaerdozent = models.ForeignKey(Person, related_name='primaerdozent', verbose_name=_("Primaerdozent"), null=True, blank=True, on_delete=models.CASCADE,
                                      help_text=_('Die Person, die im Anschreiben erwähnt wird'))
    auswertungstermin = models.DateField(null=True, blank=True,
                                         verbose_name=_('Auswertungstermin'),
                                         help_text=_('An welchem Tag sollen Fragebögen für diese Veranstaltung ausgewerter werden? ') +
                                                   _('Fragebögen die danach eintreffen werden nicht mehr ausgewertet.'))
    bestelldatum = models.DateField(null=True, blank=True)
    access_token = models.CharField(max_length=16, blank=True)
    freiefrage1 = models.TextField(verbose_name=_('1. Freie Frage'), blank=True)
    freiefrage2 = models.TextField(verbose_name=_('2. Freie Frage'), blank=True)
    kleingruppen = models.TextField(verbose_name=_('Kleingruppen'), blank=True)
    veroeffentlichen = models.BooleanField(verbose_name=_('Veroeffentlichen'), default=True, choices=BOOL_CHOICES)
    digitale_eval = models.BooleanField(default=True, verbose_name=_('Digitale Evaluation'),
                                        help_text=_('Die Evaluation soll digital durchgeführt werden. Die Studierenden füllen die Evaluation online aus.'), blank=True)
    digitale_eval_type = models.CharField(
        default='T',
        choices=DIGITALE_EVAL,
        max_length=1,
        verbose_name=_('Digitaler Evaluationstyp'),
        help_text=_('Es werden generell zwei Typen von Verteilungsmethoden angeboten: Bei TANs erhalten Sie eine Excel Datei mit einer Liste aller TANs, welche Sie beispielsweise mithilfe von moodle verteilen können (eine Anleitung dazu wird bereitgestellt). Beim losungsbasierten Verfahren erhalten Sie einen einfachen, mehrfachbenutzbaren Link zum Onlinefragebogen.')
    )

    def get_next_state(self):
        """
        Gibt den nächsten Status einer Veranstaltung zurück.
        :return: Status einer Veranstaltung
        """
        try:
            return self.STATUS_UEBERGANG[self.status][0]  # TODO: Sobald es mehrere Zustande gibt
        except KeyError:
            return None

    def set_next_state(self):
        """Setzt den nächsten Status einer Veranstaltung."""
        status = self.STATUS_UEBERGANG[self.status]

        if self.status == self.STATUS_BESTELLUNG_GEOEFFNET:
            if self.evaluieren:
                self.status = status[1]
            else:
                self.status = status[0]

        elif self.status == self.STATUS_BESTELLUNG_LIEGT_VOR:
            if self.evaluieren:
                self.status = status[1]
            else:
                self.status = status[2]

        else:
            self.status = status[0]

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
        if self.digitale_eval:
            if self.digitale_eval_type == 'L':
                result = 'codeword'
            else:
                result = 'online'
        return result

    def get_barcode_number(self, tutorgruppe=0):
        """Barcode Nummer für diese Veranstaltung"""
        if tutorgruppe > 99:
            raise ValueError(_("Tutorgruppe muss kleiner 100 sein"))

        if isinstance(tutorgruppe, int) == False:
            raise ValueError(_("Tutorgruppe muss eine ganze Zahl sein"))

        base = Veranstaltung.BARCODE_BASE
        veranst = self.pk
        code_draft = base + (veranst * 100) + tutorgruppe
        checksum = ean_checksum_calc(code_draft)

        code = (code_draft * 10) + checksum

        return code

    def get_evasys_list_veranstalter(self):
        personen = []
        if self.primaerdozent is not None:
            personen.append(self.primaerdozent)
        for per in self.ergebnis_empfaenger.all():
            if per.pk != self.primaerdozent.pk:
                personen.append(per)
        return personen

    @staticmethod
    def decode_barcode(barcode):
        if (ean_checksum_valid(barcode) != True):
            raise ValueError(_("Der Barcode ist nicht valide"))

        # entferne das Padding am Anfang
        information = barcode % Veranstaltung.BARCODE_BASE

        # entferne die checksumme
        information = information // 10

        # die letzten zwei Stellen sind die Uebungsgruppe
        tutorgroup = information % 100

        # Alle Stellen vor der Uebungsgruppe sind der PK der Veranstaltung
        veranstaltung = information // 100

        return {'veranstaltung': veranstaltung, 'tutorgroup': tutorgroup}

    def __str__(self):
        return "%s [%s] (%s)" % (self.name, self.typ, self.semester.short())

    def create_log(self, user, scanner, interface):
        """
        Erstellt einen Log wenn sich bei einer Veranstaltung etwas geändert hat.
        :param user: Über welche Benutzer die Änderung erfolgt ist.
        :param scanner: Über welchen Barcodescanner die Änderung erfolgt ist.
        :param interface: Über welches Interface die Änderung erfolgt ist.
        """
        Log.objects.create(veranstaltung=self, user=user, scanner=scanner, status=self.status, interface=interface)

    def log(self, interface, is_frontend=False):
        """
        Die Logging-Funktion
        :param interface: Über welches Interface die Änderung erfolgt ist.
        :param is_frontend: Checkt, ob die Änderung über das Frontend erfolgt ist.
        """
        if isinstance(interface, BarcodeScanner):
            self.create_log(None, interface, Log.SCANNER)
        elif isinstance(interface, User):
            if is_frontend:
                self.create_log(interface, None, Log.FRONTEND)
            else:
                self.create_log(interface, None, Log.ADMIN)

    def auwertungstermin_to_late_msg(self):
        toLateDate = self.semester.last_Auswertungstermin_to_late_human()
        return _(f'Der Auswertungstermin muss vor dem {toLateDate} liegen.')

    def has_uebung(self):
        """Gibt True zurück wenn die Veranstaltung eine Übung hat sonst False"""
        result = False
        if self.typ == 'vu':
            result = True
        return result

    def veranstalter_list(self):
        """Eine Liste aller Veranstalter dieser Veranstaltung"""
        list = [x.full_name() for x in self.veranstalter.all()]
        return ', '.join(list)
    
    
    def anzahl_too_few_msg(self) :
        return _(f'Anzahl der Bestellungen muss mindestens {self.MIN_BESTELLUNG_ANZAHL} sein. Bei weniger als {self.MIN_BESTELLUNG_ANZAHL} Teilnehmenden ist eine Evaluation leider nicht möglich')


    def clean(self, *args, **kwargs):
        super(Veranstaltung, self).clean(*args, **kwargs)

        if self.auswertungstermin is not None and self.id is not None and self.auswertungstermin > self.semester.last_Auswertungstermin().date():
            raise ValidationError(self.auwertungstermin_to_late_msg())
        
        if self.anzahl is not None and self.anzahl < self.MIN_BESTELLUNG_ANZAHL :
            raise ValidationError(self.anzahl_too_few_msg())


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
            return _("Der Veranstalter Link wird erst nach dem Anlegen angezeigt")

    def allow_order(self):
        """Überprüft anhand des Status' der Veranstaltung, ob bestellt werden darf."""
        return self.status == Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR or \
            self.status == Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET or \
            self.status == Veranstaltung.STATUS_KEINE_EVALUATION

    def csv_to_tutor(self, csv_content):
        """Erzeuge Tutoren Objekte aus der CSV Eingabe der Veranstalter"""
        input_clean = csv_content.strip()
        input_lines = input_clean.splitlines()
        nummer = 1

        Tutor.objects.filter(veranstaltung=self).delete()
        for l in input_lines:
            # skip empty lines
            if len(l.strip()) > 1:
                row = l.split(',', 3)
                # skip lines which are not well formated
                if len(row) > 1:
                    row = [x.strip() for x in row]
                    anmerkung_input = ''
                    if len(row) > 3:
                        anmerkung_input = row[3]

                    Tutor.objects.create(
                        veranstaltung=self,
                        nummer=nummer,
                        nachname=row[0],
                        vorname=row[1],
                        email=row[2],
                        anmerkung=anmerkung_input
                    )

                    nummer += 1

    class Meta:
        verbose_name = _('Veranstaltung')
        verbose_name_plural = _('Veranstaltungen')
        ordering = ['semester', 'typ', 'name']
        unique_together = ('name', 'lv_nr', 'semester')
        app_label = 'feedback'


class Tutor(models.Model):
    """Repräsentiert Tutoren für eine Veranstaltung."""
    nummer = models.PositiveSmallIntegerField()
    vorname = models.CharField(_('first name'), max_length=30)
    nachname = models.CharField(_('last name'), max_length=30)
    email = models.EmailField(_('e-mail address'))
    anmerkung = models.CharField(max_length=100)
    veranstaltung = models.ForeignKey(Veranstaltung, on_delete=models.CASCADE)

    def get_barcode_number(self):
        """Gibt die Barcodenummer anhand der Tutorennummer zurück."""
        return self.veranstaltung.get_barcode_number(tutorgruppe=self.nummer)

    def __str__(self):
        return '%s %s %d' % (self.vorname, self.nachname, self.nummer)

    class Meta:
        verbose_name = _('Tutor')
        verbose_name_plural = _('Tutoren')
        unique_together = (('nummer', 'veranstaltung'),)
        app_label = 'feedback'


class Mailvorlage(models.Model):
    """Repräsentiert eine Mailvorlage"""
    subject = models.CharField(max_length=100, unique=True)
    body = models.TextField()

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = _('Mailvorlage')
        verbose_name_plural = verbose_name + 'n'
        ordering = ['subject']
        app_label = 'feedback'


class BarcodeScanner(models.Model):
    """Repräsentiert einen Barcodescanner."""
    token = models.CharField(max_length=64, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'Barcode Scanner'
        verbose_name_plural = 'Barcode Scanner'
        app_label = 'feedback'


class BarcodeAllowedState(models.Model):
    """Repräsentiert die erlaubten Zustände für einen Barcodescanner."""
    barcode_scanner = models.ForeignKey(BarcodeScanner, on_delete=models.CASCADE)
    allow_state = models.IntegerField(choices=Veranstaltung.STATUS_CHOICES, null=True)

    class Meta:
        verbose_name = _('Erlaubter Zustand')
        verbose_name_plural = _('Erlaubte Zustände')
        unique_together = (('barcode_scanner', 'allow_state'),)
        app_label = 'feedback'


class BarcodeScannEvent(models.Model):
    """Repräsentiert einen Scan-Event für einen Barcodescanner"""
    veranstaltung = models.ForeignKey(Veranstaltung, on_delete=models.CASCADE)
    scanner = models.ForeignKey(BarcodeScanner, on_delete=models.CASCADE)
    tutorgroup = models.ForeignKey(Tutor, null=True, blank=True, on_delete=models.CASCADE)
    barcode = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'BarcodeScannEvent'
        verbose_name_plural = 'BarcodeScannEvents'
        app_label = 'feedback'

    def save(self, *args, **kwargs):
        """Extrahiere die Veranstaltungsdaten aus dem Barcode teil zwei zum ModelForm"""
        barcode_decode = Veranstaltung.decode_barcode(self.barcode)
        verst_obj = Veranstaltung.objects.get(pk=barcode_decode['veranstaltung'])
        self.veranstaltung = verst_obj
        self.veranstaltung.log(self.scanner)

        if barcode_decode['tutorgroup'] >= 1:
            tutorgroup = Tutor.objects.get(veranstaltung=verst_obj, nummer=barcode_decode['tutorgroup'])
            self.tutorgroup = tutorgroup

        super(BarcodeScannEvent, self).save(*args, **kwargs)


class Log(models.Model):
    """Repräsentiert einen Logger für die Zustandsübergänge von Veranstaltungen."""
    FRONTEND = 'fe'
    SCANNER = 'bs'
    ADMIN = 'ad'

    INTERFACE_CHOICES = (
        (FRONTEND, 'Frontend'),
        (SCANNER, 'Barcodescanner'),
        (ADMIN, 'Admin')
    )

    veranstaltung = models.ForeignKey(Veranstaltung, null=True, related_name='veranstaltung', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, related_name='user', on_delete=models.CASCADE)
    scanner = models.ForeignKey(BarcodeScanner, null=True, related_name='scanner', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=Veranstaltung.STATUS_CHOICES, default=Veranstaltung.STATUS_ANGELEGT)
    interface = models.CharField(max_length=2, choices=INTERFACE_CHOICES)

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Logs'
        app_label = 'feedback'
