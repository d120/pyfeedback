# coding=utf-8

from django.db import models

from feedback.models import Veranstaltung


class ImportPerson(models.Model):
    vorname = models.CharField(max_length=30)
    nachname = models.CharField(max_length=30)

    def full_name(self):
        return u'%s %s' % (self.vorname, self.nachname)

    def __unicode__(self):
        return u'%s, %s' % (self.nachname, self.vorname)

    class Meta:
        verbose_name = 'Importierte Person'
        verbose_name_plural = verbose_name + 'en'
        app_label = 'feedback'


class ImportCategory(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True)
    name = models.CharField(max_length=150)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Importierte Kategorie'
        verbose_name_plural = verbose_name + 'n'
        unique_together = ('parent', 'name')
        app_label = 'feedback'


class ImportVeranstaltung(models.Model):
    typ = models.CharField(max_length=1, choices=Veranstaltung.TYP_CHOICES)
    name = models.CharField(max_length=150)
    lv_nr = models.CharField(max_length=15, blank=True)
    veranstalter = models.ManyToManyField(ImportPerson, blank=True)
    category = models.ForeignKey(ImportCategory)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.lv_nr)

    class Meta:
        verbose_name = 'Importierte Veranstaltung'
        verbose_name_plural = verbose_name + 'en'
        unique_together = ('name', 'lv_nr', 'category')
        app_label = 'feedback'
