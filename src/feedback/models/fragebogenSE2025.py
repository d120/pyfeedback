
# coding=utf-8

from django.db import models
from feedback.models import Fragebogen, Ergebnis


class FragebogenSE2025(Fragebogen):
    fach = models.CharField(max_length=5, choices=Fragebogen.FACH_CHOICES, blank=True)
    abschluss = models.CharField(max_length=5, choices=Fragebogen.ABSCHLUSS_CHOICES, blank=True)
    semester = models.CharField(max_length=4, choices=Fragebogen.SEMESTER_CHOICES16, blank=True)
    geschlecht = models.CharField(max_length=1, choices=Fragebogen.GESCHLECHT_CHOICES, blank=True)
    studienberechtigung = models.CharField(max_length=1, choices=Fragebogen.STUDIENBERECHTIGUNG_CHOICES, blank=True)
    male_veranstaltung_gehoert = models.CharField(max_length=1, choices=Fragebogen.VERANSTALTUNG_GEHOERT, blank=True)

    s_wie_oft_besucht = models.PositiveSmallIntegerField(blank=True, null=True)
    s_besuch_ueberschneidung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_besuch_qualitaet = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_besuch_verhaeltnisse = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_besuch_privat = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_besuch_elearning = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_besuch_zufrueh = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_besuch_sonstiges = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)

    s_3_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_8 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_9 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_3_10 = models.PositiveSmallIntegerField(blank=True, null=True)

    s_4_1 = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_4_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_4_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_4_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_4_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_4_6 = models.CharField(max_length=1, choices=Fragebogen.STUNDEN_NACHBEARBEITUNG, blank=True)

    s_5_1 = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    s_5_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_5_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_5_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_5_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_5_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_5_7 = models.CharField(max_length=1, choices=Fragebogen.STUNDEN_NACHBEARBEITUNG, blank=True)

    s_6_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_8 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_9 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_6_10 = models.PositiveSmallIntegerField(blank=True, null=True)

    s_7_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_7_2 = models.PositiveSmallIntegerField(blank=True, null=True)

    s_9_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_9_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_9_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_9_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    s_9_5 = models.PositiveSmallIntegerField(blank=True, null=True)

    # after adding 'prize recommendation' question complete this
    # s_9_ = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)

    class Meta:
        verbose_name = 'Seminarfragebogen 2025'
        verbose_name_plural = 'Seminarfragebögen 2025'
        ordering = ['semester', 'veranstaltung']
        app_label = 'feedback'


class ErgebnisSE2025(Ergebnis):
    parts = [
        [
            's_9_5', 'Seminar: Gesamtnote',
            [
                '9.5 Welche Gesamtnote gibst du dem Seminar?',
            ]
        ],
        [
            's_didaktik', 'Seminar: Didaktik',
            [
                '3.4 Das Seminar war eine gute Mischung aus Wissensvermittlung und Diskussion.',
                '3.8 Es wurde ausreichend konstruktives Feedback gegeben.',
                '3.9 Das Seminar hat mich dazu motiviert, mich weiter mit dem Thema zu beschäftigen.',
                '5.3 Der Umfang der Ausarbeitungen war angemessen.',
                '5.4 Während der Erstellung der Ausarbeitung gab es ausreichende Unterstützung durch die Veranstalter*innen.',
                '6.3 Die Lehrkraft hat bei Problemen kompetente Unterstützung bieten können.',
                '6.4 Die Lehrkraft war engagiert.',
                '6.5 Die Lehrkraft ist auf studentische Fragen und Beiträge angemessen eingegangen.',
                '6.6 Die Lehrkraft hat die Diskussionen gut geleitet. ',
                '6.7 Die Lehrkraft regte uns gezielt zum Mitdenken und eigener Mitarbeit an.',
                '6.9 Die Lehrkraft hat die Veranstaltung gut und angemessen betreut.',
            ]
        ],
        [
            's_organisation', 'Seminar: Organisation',
            [
                '3.1 Das Seminar war inhaltlich gut strukturiert.',
                '3.2 Die Organisation des Seminars war gut.',
                '3.5 Für die Diskussionen der Themen war genug Zeit.',
                '3.7 Es wurden ausreichend Materialien zur Verfügung gestellt.',
                '4.2 Die Kriterien (Inhalt, Aufbau, Präsentation) für ein gutes Referat wurden verdeutlicht.',
                '4.4 Referate waren eine sinnvolle Weise, um den Teilnehmer*innen die Inhalte zu vermitteln.',
                '4.5 Die Zeitpunkte für die Referate waren gut vereinbar mit anderen Veranstaltungen und Klausurterminen.',
                '5.2 Die Kriterien für eine gute Ausarbeitung wurden verdeutlicht.',
                '5.6 Die Zeitpunkte für die Abgabe von Ausarbeitungen waren gut vereinbar mit anderen Veranstaltungen und Klausurterminen.',
                '6.1 Die Lehrkraft hat eine gute Einführung in die Thematik gegeben.',
            ]
        ],
        [
            's_praxisbezug_motivation', 'Seminar: Praxisbezug und Motivation',
            [
                '3.10 Durch das Seminar konnte ich meine Vortragstechnik verfeinern.',
                '5.5 Durch das Anfertigen der Ausarbeitungen habe ich einen umfassenden Einblick in das Thema erhalten.',
            ]
        ],
        [
            's_digitale_lehre', 'Seminar: Digitale Lehre',
            [
                '6.8 Die Lehrkraft setzte verfügbare Medien sinnvoll ein.',
                '7.1 Ich habe ausreichend Informationen zur Nutzung des digitalen Lehr-/Lernangebots von dem/der Lehrenden erhalten.',
                '7.2 Mir ist es technisch möglich, in vollem Umfang an der Veranstaltung teilzunehmen.',
            ]
        ],
    ]

    hidden_parts = [
        [
            's_feedbackpreis', 'Feedbackpreis: Bestes Seminar',
            [
                '3.1 Das Seminar war inhaltlich gut strukturiert.',
                '3.7 Es wurden ausreichend Materialien zur Verfügung gestellt.',
                '3.8 Es wurde ausreichend konstruktives Feedback gegeben.',
                '3.9 Das Seminar hat mich dazu motiviert, mich weiter mit dem Thema zu beschäftigen.',
                '4.2 Die Kriterien (Inhalt, Aufbau, Präsentation) für ein gutes Referat wurden verdeutlicht.',
                '5.4 Während der Erstellung der Ausarbeitung gab es ausreichende Unterstützung durch die Veranstalter*innen.',
                '6.3 Die Lehrkraft hat bei Problemen kompetente Unterstützung bieten können.',
                '6.4 Die Lehrkraft war engagiert.',
                '6.7 Die Lehrkraft regte uns gezielt zum Mitdenken und eigener Mitarbeit an.',
                '6.8 Die Lehrkraft setzte verfügbare Medien sinnvoll ein.',
                '9.5 Welche Gesamtnote gibst du dem Seminar?',
            ]
        ]
    ]

    weight = {} # adjust weight for ranking 


    # TODO: decimal statt float benutzen
    s_didaktik = models.FloatField(blank=True, null=True)
    s_didaktik_count = models.PositiveIntegerField(default=0)
    s_didaktik_parts = ['s_3_4', 's_3_8', 's_3_9', 's_5_3', 's_5_4', 's_6_3', 's_6_4', 's_6_5', 's_6_6', 's_6_7', 's_6_7', 's_6_9',]

    s_organisation = models.FloatField(blank=True, null=True)
    s_organisation_count = models.PositiveIntegerField(default=0)
    s_organisation_parts = ['s_3_1', 's_3_2', 's_3_5', 's_3_7', 's_4_2', 's_4_4', 's_4_5', 's_5_2', 's_5_6', 's_6_1',]

    s_praxisbezug_motivation = models.FloatField(blank=True, null=True)
    s_praxisbezug_motivation_count = models.PositiveIntegerField(default=0)
    s_praxisbezug_motivation_parts = ['s_3_10', 's_5_5',]

    s_digitale_lehre = models.FloatField(blank=True, null=True)
    s_digitale_lehre_count = models.PositiveIntegerField(default=0)
    s_digitale_lehre_parts = ['s_6_8', 's_7_1', 's_7_2',]

    s_9_5 = models.FloatField(blank=True, null=True)
    s_9_5_count = models.PositiveIntegerField(default=0)

    s_feedbackpreis = models.FloatField(blank=True, null=True)
    s_feedbackpreis_count = models.PositiveIntegerField(default=0)
    s_feedbackpreis_parts = [
        's_3_1', 's_3_7', 's_3_8', 's_3_9', 's_4_2', 's_5_4', 's_6_3', 's_6_4', 's_6_7', 's_6_8', 's_9_5',
    ]

    gesamt = models.FloatField(blank=True, null=True)
    gesamt_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Seminarergebnis 2025'
        verbose_name_plural = 'Seminarergebnisse 2025'
        ordering = ['veranstaltung']
        app_label = 'feedback'
