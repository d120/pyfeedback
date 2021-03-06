# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-23 16:21


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0021_merge_20161215_1708'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barcodeallowedstate',
            name='allow_state',
            field=models.IntegerField(choices=[(100, 'Angelegt'), (600, 'Gedruckt'), (700, 'Versandt'), (800, 'B\xf6gen eingegangen'), (900, 'B\xf6gen gescannt'), (1000, 'Ergebnisse versandt')], null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='status',
            field=models.IntegerField(choices=[(100, 'Angelegt'), (600, 'Gedruckt'), (700, 'Versandt'), (800, 'B\xf6gen eingegangen'), (900, 'B\xf6gen gescannt'), (1000, 'Ergebnisse versandt')], default=100),
        ),
        migrations.AlterField(
            model_name='veranstaltung',
            name='status',
            field=models.IntegerField(choices=[(100, 'Angelegt'), (600, 'Gedruckt'), (700, 'Versandt'), (800, 'B\xf6gen eingegangen'), (900, 'B\xf6gen gescannt'), (1000, 'Ergebnisse versandt')], default=100),
        ),
    ]
