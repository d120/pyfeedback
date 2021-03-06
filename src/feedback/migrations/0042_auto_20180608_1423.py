# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-08 14:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0041_auto_20180525_1722'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailEndung',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=150, null=True)),
                ('fachgebiet', models.ForeignKey(blank=True, help_text='Hier soll der Domainname einer Email-Adresse eines Fachgebiets stehen.', on_delete=django.db.models.deletion.CASCADE, to='feedback.Fachgebiet')),
            ],
            options={
                'verbose_name': 'Fachgebiet Emailendung',
                'verbose_name_plural': 'Fachgebiet Emailendungen',
            },
        ),
        migrations.RemoveField(
            model_name='fachgebietemail',
            name='email_suffix',
        ),
    ]
