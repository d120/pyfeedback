# coding=utf-8

from django.db import models
from feedback.models import Fragebogen, Ergebnis


class Fragebogen2008(Fragebogen):
    fach = models.CharField(max_length=5, choices=Fragebogen.FACH_CHOICES, blank=True)
    abschluss = models.CharField(max_length=5, choices=Fragebogen.ABSCHLUSS_CHOICES, blank=True)
    semester = models.PositiveSmallIntegerField(blank=True, null=True)

    v_wie_oft_besucht = models.PositiveSmallIntegerField(blank=True, null=True)
    v_besuch_ueberschneidung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_verhaeltnisse = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_qualitaet = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_privat = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_besuch_sonstiges = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    v_a = models.PositiveSmallIntegerField(blank=True, null=True)
    v_b = models.PositiveSmallIntegerField(blank=True, null=True)
    v_c = models.PositiveSmallIntegerField(blank=True, null=True)
    v_d = models.PositiveSmallIntegerField(blank=True, null=True)
    v_e = models.PositiveSmallIntegerField(blank=True, null=True)
    v_f = models.PositiveSmallIntegerField(blank=True, null=True)
    v_f2 = models.CharField(max_length=1, choices=Fragebogen.GESCHWINDIGKEIT_CHOICES, blank=True)
    v_g = models.PositiveSmallIntegerField(blank=True, null=True)
    v_h = models.PositiveSmallIntegerField(blank=True, null=True)
    v_i = models.PositiveSmallIntegerField(blank=True, null=True)
    v_j = models.PositiveSmallIntegerField(blank=True, null=True)
    v_k = models.PositiveSmallIntegerField(blank=True, null=True)
    v_l = models.PositiveSmallIntegerField(blank=True, null=True)
    v_m = models.PositiveSmallIntegerField(blank=True, null=True)
    v_gesamt = models.PositiveSmallIntegerField(blank=True, null=True)

    ue_wie_oft_besucht = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_besuch_ueberschneidung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_verhaeltnisse = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_qualitaet = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_privat = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_sonstiges = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_a = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_b = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_c = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_d = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_e = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_f = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_g = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_h = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_i = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_i2 = models.CharField(max_length=1, choices=Fragebogen.NIVEAU_CHOICES, blank=True)
    ue_j = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_gesamt = models.PositiveSmallIntegerField(blank=True, null=True)

    zusaetzliche_zeit = models.PositiveSmallIntegerField(blank=True, null=True)
    vorwissen_aussreichend = models.PositiveSmallIntegerField(blank=True, null=True)
    empfehlung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)

    class Meta:
        verbose_name = 'Fragebogen 2008'
        verbose_name_plural = 'Fragebögen 2008'
        ordering = ['semester', 'veranstaltung']
        app_label = 'feedback'


class Ergebnis2008(Ergebnis):
    parts_vl = [
        ['v_gesamt', 'Vorlesung: Gesamtnote',
         ['2.4 Welche Gesamtnote würdest Du der Vorlesung (ohne Übungen) geben?']],
        ['v_didaktik', 'Vorlesung: Didaktik',
         ['2.3b Der/Die Dozent/in hat Kompliziertes verständlich dargelegt.',
          '2.3c Der Stoff wurde anhand von Beispielen verdeutlicht.',
          '2.3f Das Tempo der Vorlesung war angemessen.',
          '2.3h Der/Die Dozent/in war enthusiastisch und schaffte es, den Funken überspringen zu lassen.',
          '2.3l Die Hilfsmittel (Skript, Lehrbücher, Literaturangaben, Folien) haben mein Lernen wirkungsvoll unterstützt.',
          '2.3m Der Tafelanschrieb / die Folien waren geeignet, den Lernprozess zu unterstützen (Stichwort: Lesbarkeit, Verständlichkeit).']],
        ['v_organisation', 'Vorlesung: Organisation',
         ['2.3a Die Vorlesung war gut strukturiert, ein roter Faden war erkennbar.',
          '2.3g Der/Die Dozent/in zeigte sich gut vorbereitet.',
          '2.3i Die (Zwischen-)Fragen der Studierenden wurden angemessen beantwortet.',
          '2.3j Der/Die Dozent/in war auch außerhalb der Veranstaltung ansprechbar.']],
        ['v_praxisbezug_motivation', 'Vorlesung: Praxisbezug und Motivation',
         ['2.3d Der/Die Dozent/in zeigte Bezüge zur aktuellen Forschung auf.',
          '2.3e Der Bezug zwischen Theorie und praktischem Arbeiten / praktischen Anwendungen wurde hergestellt.',
          '2.3k Die Vorlesung motivierte mich dazu, mich selbstständig mit den behandelten Themengebieten auseinanderzusetzen.']],
    ]
    parts_ue = [
        ['ue_gesamt', 'Übung: Gesamtnote',
         ['3.4 Welche Gesamtnote würdest Du der Übung geben?']],
        ['ue_aufgaben', 'Übung: Aufgaben',
         ['3.3a Die Übungen hatten jeweils eine klare Struktur.',
          '3.3b Durch die Übungen und die Aufgaben habe ich viel gelernt.',
          '3.3c Die Übungen waren sehr motivierend.',
          '3.3i Das Anspruchsniveau der Aufgabenstellungen war angemessen.']],
        ['ue_organisation', 'Übung: Organisation',
         ['3.3d Der Stoff der Übungen war immer gut mit dem Stoff der Vorlesung abgestimmt.',
          '3.3g Die Größe der Gruppen in den Übungen war angemessen.',
          '3.3h Der Raum für die Übungen war zum Arbeiten und Lernen geeignet.',
          '3.3j Die Organisation des Übungsbetriebs (Hausübungen, Testate) war gut.']],
        ['ue_betreuung', 'Übung: Betreuung',
         ['3.3e Die Übungsbetreuung (Mitarbeiter/innen, Hiwis) war gut.',
          '3.3f Der/Die Dozent/in hat elektronische Plattformen (Foren, Mailinglisten, Wiki, Websites) sinnvoll und hilfreich eingesetzt.']],
    ]
    parts = parts_vl + parts_ue
    hidden_parts = [
        ['v_feedbackpreis', 'Feedbackpreis: Beste Vorlesung',
         ['2.3a Die Vorlesung war gut strukturiert, ein roter Faden war erkennbar.',
          '2.3b Der/Die Dozent/in hat Kompliziertes verständlich dargelegt.',
          '2.3c Der Stoff wurde anhand von Beispielen verdeutlicht.',
          '2.3d Der/Die Dozent/in zeigte Bezüge zur aktuellen Forschung auf.',
          '2.3e Der Bezug zwischen Theorie und praktischem Arbeiten / praktischen Anwendungen wurde hergestellt.',
          '2.3f Das Tempo der Vorlesung war angemessen.',
          '2.3g Der/Die Dozent/in zeigte sich gut vorbereitet.',
          '2.3h Der/Die Dozent/in war enthusiastisch und schaffte es, den Funken überspringen zu lassen.',
          '2.3i Die (Zwischen-)Fragen der Studierenden wurden angemessen beantwortet.',
          '2.3k Die Vorlesung motivierte mich dazu, mich selbstständig mit den behandelten Themengebieten auseinanderzusetzen.',
          '2.3l Die Hilfsmittel (Skript, Lehrbücher, Literaturangaben, Folien) haben mein Lernen wirkungsvoll unterstützt.',
          '2.3m Der Tafelanschrieb / die Folien waren geeignet, den Lernprozess zu unterstützen (Stichwort: Lesbarkeit, Verständlichkeit).',
          '2.4 Welche Gesamtnote würdest Du der Vorlesung (ohne Übungen) geben?']],
        ['ue_feedbackpreis', 'Feedbackpreis: Beste Übung',
         ['3.3a Die Übungen hatten jeweils eine klare Struktur.',
          '3.3b Durch die Übungen und die Aufgaben habe ich viel gelernt.',
          '3.3c Die Übungen waren sehr motivierend.',
          '3.3d Der Stoff der Übungen war immer gut mit dem Stoff der Vorlesung abgestimmt.',
          '3.3e Die Übungsbetreuung (Mitarbeiter/innen, Hiwis) war gut.',
          '3.3f Der/Die Dozent/in hat elektronische Plattformen (Foren, Mailinglisten, Wiki, Websites) sinnvoll und hilfreich eingesetzt.',
          '3.3g Die Größe der Gruppen in den Übungen war angemessen.',
          '3.3i Das Anspruchsniveau der Aufgabenstellungen war angemessen.',
          '3.3j Die Organisation des Übungsbetriebs (Hausübungen, Testate) war gut.',
          '3.4 Welche Gesamtnote würdest Du der Übung geben?']],
    ]
    weight = {
        'v_feedbackpreis': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 12],
        'ue_feedbackpreis': [1, 1, 1, 1, 1, 1, 1, 1, 1, 10],
    }

    v_didaktik = models.FloatField(blank=True, null=True)
    v_didaktik_count = models.PositiveIntegerField(default=0)
    v_didaktik_parts = ['v_b', 'v_c', 'v_f', 'v_h', 'v_l', 'v_m']
    v_organisation = models.FloatField(blank=True, null=True)
    v_organisation_count = models.PositiveIntegerField(default=0)
    v_organisation_parts = ['v_a', 'v_g', 'v_i', 'v_j']
    v_praxisbezug_motivation = models.FloatField(blank=True, null=True)
    v_praxisbezug_motivation_count = models.PositiveIntegerField(default=0)
    v_praxisbezug_motivation_parts = ['v_d', 'v_e', 'v_k']
    v_gesamt = models.FloatField(blank=True, null=True)
    v_gesamt_count = models.PositiveIntegerField(default=0)

    v_feedbackpreis = models.FloatField(blank=True, null=True)
    v_feedbackpreis_count = models.PositiveIntegerField(default=0)
    v_feedbackpreis_parts = ['v_a', 'v_b', 'v_c', 'v_d', 'v_e', 'v_f', 'v_g', 'v_h', 'v_i', 'v_k', 'v_l', 'v_m',
                             'v_gesamt']

    ue_aufgaben = models.FloatField(blank=True, null=True)
    ue_aufgaben_count = models.PositiveIntegerField(default=0)
    ue_aufgaben_parts = ['ue_a', 'ue_b', 'ue_c', 'ue_i']
    ue_organisation = models.FloatField(blank=True, null=True)
    ue_organisation_count = models.PositiveIntegerField(default=0)
    ue_organisation_parts = ['ue_d', 'ue_g', 'ue_h', 'ue_j']
    ue_betreuung = models.FloatField(blank=True, null=True)
    ue_betreuung_count = models.PositiveIntegerField(default=0)
    ue_betreuung_parts = ['ue_e', 'ue_f']
    ue_gesamt = models.FloatField(blank=True, null=True)
    ue_gesamt_count = models.PositiveIntegerField(default=0)

    ue_feedbackpreis = models.FloatField(blank=True, null=True)
    ue_feedbackpreis_count = models.PositiveIntegerField(default=0)
    ue_feedbackpreis_parts = ['ue_a', 'ue_b', 'ue_c', 'ue_d', 'ue_e', 'ue_f', 'ue_g', 'ue_i', 'ue_j', 'ue_gesamt']

    class Meta:
        verbose_name = 'Ergebnis 2008'
        verbose_name_plural = 'Ergebnisse 2008'
        ordering = ['veranstaltung']
        app_label = 'feedback'
