# coding=utf-8

from django.db import models
from feedback.models import Fragebogen, Ergebnis

class Fragebogen2012(Fragebogen):
    fach = models.CharField(max_length=5, choices=Fragebogen.FACH_CHOICES, blank=True)
    abschluss = models.CharField(max_length=5, choices=Fragebogen.ABSCHLUSS_CHOICES, blank=True)
    semester = models.CharField(max_length=3, choices=Fragebogen.SEMESTER_CHOICES, blank=True)
    geschlecht = models.CharField(max_length=1, choices=Fragebogen.GESCHLECHT_CHOICES, blank=True)
    studienberechtigung = models.CharField(max_length=1, choices=Fragebogen.STUDIENBERECHTIGUNG_CHOICES, blank=True)
    
    v_wie_oft_besucht = models.PositiveSmallIntegerField(blank=True, null=True)
    v_besuch_ueberschneidung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_qualitaet = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_verhaeltnisse = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_privat = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_sonstiges = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_8 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_9 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_10 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_10a = models.CharField(max_length=1, choices=Fragebogen.GESCHWINDIGKEIT_CHOICES, blank=True)
    v_11 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_12 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_13 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_14 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_15 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_16 = models.PositiveSmallIntegerField(blank=True, null=True)
    v_gesamt = models.PositiveSmallIntegerField(blank=True, null=True)
    
    ue_wie_oft_besucht = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_besuch_ueberschneidung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_qualitaet = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_verhaeltnisse = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_privat = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_sonstiges = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_8 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_9 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_10 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_11 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_12 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_13 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_13a = models.CharField(max_length=1, choices=Fragebogen.NIVEAU_CHOICES, blank=True)
    ue_14 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_15 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_gesamt = models.PositiveSmallIntegerField(blank=True, null=True)
    
    zusaetzliche_zeit = models.PositiveSmallIntegerField(blank=True, null=True)
    vorwissen_aussreichend = models.PositiveSmallIntegerField(blank=True, null=True)
    empfehlung = models.PositiveSmallIntegerField(blank=True, null=True)

    gesamt = models.PositiveSmallIntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Fragebogen 2012'
        verbose_name_plural = 'Fragebögen 2012'
        ordering = ['semester', 'veranstaltung']
        app_label = 'feedback'
    

class Ergebnis2012(Ergebnis):
    parts_vl = [
             ['gesamt', 'Gesamtveranstaltung: Gesamtnote',
              ['Welche Note gibst Du der Lehrveranstaltung insgesamt?']],
             ['empfehlung', 'Gesamtveranstaltung: Empfehlungen',
              ['4.3 Ich würde die Vorlesung einer Freundin / einem Freund empfehlen.']],
             ['v_gesamt', 'Vorlesung: Gesamtnote',
              ['Welche Gesamtnote würdest Du der Vorlesung (ohne Übungen) geben?']], 
             ['v_didaktik', 'Vorlesung: Didaktik',
              ['2.6 Die Lehrkraft hat Kompliziertes verständlich dargelegt.',
               '2.7 Der Stoff wurde anhand von Beispielen verdeutlicht.',
               '2.10 Das Tempo der Vorlesung war angemessen.',
               '2.14 Der Lehrende regte gezielt zur eigenen Mitarbeit / zum Mitdenken in der Veranstaltung an.',
               '2.16 Die Vorlesungsmaterialien (Folien, Skripte, Tafelanschrieb, Lehrbücher etc.) haben das Lernen wirkungsvoll unterstützt.']],
             ['v_organisation', 'Vorlesung: Organisation',
              ['2.4 Die Vorlesung war inhaltlich gut strukturiert, ein roter Faden war erkennbar.',
               '2.5 Die Lernziele der Veranstaltung sind mir klar geworden.',
               '2.11 Die Lehrkraft zeigte sich gut vorbereitet.',
               '2.12 Die (Zwischen-)Fragen der Studierenden wurden angemessen beantwortet.',
               '2.13 Der Lehrende war auch außerhalb der Veranstaltung ansprechbar.']],
             ['v_praxisbezug_motivation', 'Vorlesung: Praxisbezug und Motivation',
              ['2.8 Die Lehrkraft zeigte Bezüge zur aktuellen Forschung auf.',
               '2.9 Der Bezug zwischen Theorie und praktischem Arbeiten / praktischen Anwendungen wurde hergestellt.',
               '2.15 Die Vorlesung motivierte dazu, sich außerhalb der Veranstaltung selbstständig mit den behandelten Themen auseinanderzusetzen.']],
            ]
    parts_ue = [
             ['ue_gesamt', 'Übung: Gesamtnote',
              ['Welche Gesamtnote würdest Du der Übung geben?']],
             ['ue_aufgaben', 'Übung: Aufgaben',
              ['3.4 Die Übungen hatten jeweils eine klare Struktur.',
               '3.5 Durch die Übungen und die Aufgaben habe ich viel gelernt.',
               '3.6 Die Übungen waren sehr motivierend.',
               '3.13 Das Anspruchsniveau der Aufgabenstellungen war angemessen.',
               '3.15 Es wurde genug Übungsmaterial (Aufgaben etc.) zur Verfügung gestellt.']],
             ['ue_organisation', 'Übung: Organisation',
              ['3.8 Der Stoff der Übungen war immer gut mit dem Stoff der Vorlesung abgestimmt.',
               '3.11 Die Größe der Gruppen in den Übungen war angemessen.',
               '3.12 Der Raum für die Übungen war zum Arbeiten und Lernen geeignet.',
               '3.14 Die Organisation des Übungsbetriebs (Hausübungen, Testate) war gut.']],
             ['ue_betreuung', 'Übung: Betreuung',
              ['3.7 Die Übungsbetreuung (Mitarbeiter/innen, Hiwis) war gut.',
               '3.9 Die Lehrkraft hat elektronische Plattformen (Foren, Mailinglisten, Wiki, Websites) sinnvoll und hilfreich eingesetzt.',
               '3.10 Die Betreuungsrelation war zufriedenstellend.']],                
            ]
    parts = parts_vl + parts_ue
    hidden_parts = [
             ['v_feedbackpreis', 'Feedbackpreis: Beste Vorlesung',
              ['2.4 Die Vorlesung war inhaltlich gut strukturiert, ein roter Faden war erkennbar.',
               '2.5 Die Lernziele der Veranstaltung sind mir klar geworden.',
               '2.6 Die Lehrkraft hat Kompliziertes verständlich dargelegt.',
               '2.7 Der Stoff wurde anhand von Beispielen verdeutlicht.',
               '2.8 Die Lehrkraft zeigte Bezüge zur aktuellen Forschung auf.',
               '2.9 Der Bezug zwischen Theorie und praktischem Arbeiten / praktischen Anwendungen wurde hergestellt.',
               '2.10 Das Tempo der Vorlesung war angemessen.',
               '2.11 Die Lehrkraft zeigte sich gut vorbereitet.',
               '2.12 Die (Zwischen-)Fragen der Studierenden wurden angemessen beantwortet.',
               '2.13 Der Lehrende war auch außerhalb der Veranstaltung ansprechbar.',
               '2.14 Der Lehrende regte gezielt zur eigenen Mitarbeit / zum Mitdenken in der Veranstaltung an.',
               '2.15 Die Vorlesung motivierte dazu, sich außerhalb der Veranstaltung selbstständig mit den behandelten Themen auseinanderzusetzen.',
               '2.16 Die Vorlesungsmaterialien (Folien, Skripte, Tafelanschrieb, Lehrbücher etc.) haben das Lernen wirkungsvoll unterstützt.',
               'Welche Gesamtnote würdest Du der Vorlesung (ohne Übungen) geben?']], 
             ['ue_feedbackpreis', 'Feedbackpreis: Beste Übung',
              ['3.4 Die Übungen hatten jeweils eine klare Struktur.',
               '3.5 Durch die Übungen und die Aufgaben habe ich viel gelernt.',
               '3.6 Die Übungen waren sehr motivierend.',
               '3.7 Die Übungsbetreuung (Mitarbeiter/innen, Hiwis) war gut.',
               '3.8 Der Stoff der Übungen war immer gut mit dem Stoff der Vorlesung abgestimmt.',
               '3.9 Die Lehrkraft hat elektronische Plattformen (Foren, Mailinglisten, Wiki, Websites) sinnvoll und hilfreich eingesetzt.',
               '3.11 Die Größe der Gruppen in den Übungen war angemessen.',
               '3.13 Das Anspruchsniveau der Aufgabenstellungen war angemessen.',
               '3.14 Die Organisation des Übungsbetriebs (Hausübungen, Testate) war gut.',
               '3.15 Es wurde genug Übungsmaterial (Aufgaben etc.) zur Verfügung gestellt.',
               'Welche Gesamtnote würdest Du der Übung geben?']],
            ]
    weight = {
              'v_feedbackpreis': [1] * 13 + [13],
              'ue_feedbackpreis': [1] * 10 + [10],
             }
    
    #TODO: decimal statt float benutzen
    v_didaktik = models.FloatField(blank=True, null=True)
    v_didaktik_count = models.PositiveIntegerField(default=0)
    v_didaktik_parts = ['v_6', 'v_7', 'v_10', 'v_14', 'v_16']
    v_organisation = models.FloatField(blank=True, null=True)
    v_organisation_count = models.PositiveIntegerField(default=0)
    v_organisation_parts = ['v_4', 'v_5', 'v_11', 'v_12', 'v_13']
    v_praxisbezug_motivation = models.FloatField(blank=True, null=True)
    v_praxisbezug_motivation_count = models.PositiveIntegerField(default=0)
    v_praxisbezug_motivation_parts = ['v_8', 'v_9', 'v_15']
    v_gesamt = models.FloatField(blank=True, null=True)
    v_gesamt_count = models.PositiveIntegerField(default=0)
    empfehlung = models.FloatField(blank=True, null=True)
    empfehlung_count = models.PositiveIntegerField(default=0)
    
    v_feedbackpreis = models.FloatField(blank=True, null=True)
    v_feedbackpreis_count = models.PositiveIntegerField(default=0)
    v_feedbackpreis_parts = ['v_4', 'v_5', 'v_6', 'v_7', 'v_8', 'v_9', 'v_10', 'v_11', 'v_12', 'v_13', 'v_14', 'v_15', 'v_16', 'v_gesamt']

    ue_aufgaben = models.FloatField(blank=True, null=True)
    ue_aufgaben_count = models.PositiveIntegerField(default=0)
    ue_aufgaben_parts = ['ue_4', 'ue_5', 'ue_6', 'ue_13', 'ue_15']
    ue_organisation = models.FloatField(blank=True, null=True)
    ue_organisation_count = models.PositiveIntegerField(default=0)
    ue_organisation_parts = ['ue_8', 'ue_11', 'ue_12', 'ue_14']
    ue_betreuung = models.FloatField(blank=True, null=True)
    ue_betreuung_count = models.PositiveIntegerField(default=0)
    ue_betreuung_parts = ['ue_7', 'ue_9', 'ue_10']
    ue_gesamt = models.FloatField(blank=True, null=True)
    ue_gesamt_count = models.PositiveIntegerField(default=0)

    ue_feedbackpreis = models.FloatField(blank=True, null=True)
    ue_feedbackpreis_count = models.PositiveIntegerField(default=0)
    ue_feedbackpreis_parts = ['ue_4', 'ue_5', 'ue_6', 'ue_7', 'ue_8', 'ue_9', 'ue_11', 'ue_13', 'ue_14', 'ue_15', 'ue_gesamt']

    gesamt = models.FloatField(blank=True, null=True)
    gesamt_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Ergebnis 2012'
        verbose_name_plural = 'Ergebnisse 2012'
        ordering = ['veranstaltung']
        app_label = 'feedback'
