# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-11-11 14:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0044_auto_20191106_1734'),
    ]

    operations = [
        migrations.AddField(
            model_name='semester',
            name='standard_ergebnisversand',
            field=models.DateField(blank=True, help_text='Standarddatum für den Ergebnisversand', null=True, verbose_name='Ergebnisversand'),
        ),
    ]