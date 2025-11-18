from django.db import models
from feedback.models import Fragebogen


class FragebogenUE2025(Fragebogen):
    fach = models.CharField(max_length=5, choices=Fragebogen.FACH_CHOICES, blank=True)
    abschluss = models.CharField(max_length=5, choices=Fragebogen.ABSCHLUSS_CHOICES, blank=True)
    semester = models.CharField(max_length=4, choices=Fragebogen.SEMESTER_CHOICES16, blank=True)
    geschlecht = models.CharField(max_length=1, choices=Fragebogen.GESCHLECHT_CHOICES, blank=True)
    studienberechtigung = models.CharField(max_length=1, choices=Fragebogen.STUDIENBERECHTIGUNG_CHOICES, blank=True)

    ue_wie_oft_besucht = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_besuch_ueberschneidung = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_qualitaet = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_verhaeltnisse = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_privat = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_elearning = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_zufrueh = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)
    ue_besuch_sonstiges = models.CharField(max_length=1, choices=Fragebogen.BOOLEAN_CHOICES, blank=True)

    ue_3_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_3_8 = models.PositiveSmallIntegerField(blank=True, null=True)

    ue_4_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_8 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_9 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_4_10 = models.CharField(max_length=1, blank=True)
    ue_4_11 = models.CharField(max_length=1, blank=True)

    kennziffer = models.PositiveSmallIntegerField(blank=True, null=True)

    ue_5_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_3 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_4 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_5 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_6 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_7 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_8 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_9 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_10 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_11 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_12 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_13 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_14 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_15 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_5_16 = models.PositiveSmallIntegerField(blank=True, null=True)

    ue_6_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_6_2 = models.PositiveSmallIntegerField(blank=True, null=True)

    ue_7_1 = models.CharField(max_length=1, choices=Fragebogen.STUNDEN_NACHBEARBEITUNG, blank=True)
    ue_7_2 = models.PositiveSmallIntegerField(blank=True, null=True)
    ue_7_3 = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Übungsfragebogen 2025'
        verbose_name_plural = 'Übungsfragebögen 2025'
        ordering = ['semester', 'veranstaltung']
        app_label = 'feedback'
