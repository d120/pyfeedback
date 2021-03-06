# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 18:54


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0033_auto_20170125_1009'),
    ]

    operations = [
        migrations.AddField(
            model_name='veranstaltung',
            name='veroeffentlichen',
            field=models.BooleanField(choices=[(True, 'Ja'), (False, 'Nein')], default=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='anschrift',
            field=models.CharField(blank=True, help_text='Tragen Sie bitte nur die Anschrift ohne Namen ein, da der Name automatisch hinzugef\xfcgt wird.', max_length=80, verbose_name='anschrift'),
        ),
        migrations.AlterField(
            model_name='person',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='E-Mail'),
        ),
    ]
