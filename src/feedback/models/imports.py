# coding=utf-8

from django.db import models

from feedback.models import Veranstaltung


class ImportPerson(models.Model):
    vorname = models.CharField(max_length=30)
    nachname = models.CharField(max_length=30)

    def full_name(self):
        return '%s %s' % (self.vorname, self.nachname)

    def __str__(self):
        return '%s, %s' % (self.nachname, self.vorname)

    class Meta:
        verbose_name = 'Importierte Person'
        verbose_name_plural = verbose_name + 'en'
        app_label = 'feedback'


class ImportCategory(models.Model):
    name = models.CharField(max_length=150)

    # gibt die rekursionstiefe im baum an.
    # nullable, um root-Kategorie besonders zu behandeln
    rel_level = models.IntegerField(null=True, default=0)

    # um eindeutige Suche nach Kategorie zu ermoeglichen
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Importierte Kategorie'
        verbose_name_plural = verbose_name + 'n'
        app_label = 'feedback'
        unique_together = ('parent', 'name')


class ImportVeranstaltung(models.Model):
    typ = models.CharField(max_length=1, choices=Veranstaltung.TYP_CHOICES)
    name = models.CharField(max_length=150)
    lv_nr = models.CharField(max_length=15, blank=True)
    veranstalter = models.ManyToManyField(ImportPerson, blank=True)
    category = models.ForeignKey(ImportCategory, related_name="ivs", on_delete=models.CASCADE)
    is_attended_course = models.BooleanField(default=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.lv_nr)

    class Meta:
        verbose_name = 'Importierte Veranstaltung'
        verbose_name_plural = verbose_name + 'en'
        unique_together = ('name', 'lv_nr', 'category')
        app_label = 'feedback'
