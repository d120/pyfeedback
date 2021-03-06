# Generated by Django 2.2.12 on 2020-05-25 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0045_semester_standard_ergebnisversand'),
    ]

    operations = [
        migrations.AddField(
            model_name='veranstaltung',
            name='digitale_eval_type',
            field=models.CharField(choices=[('T', 'TANs'), ('L', 'Losung')], default='T', max_length=1),
        ),
        migrations.AlterField(
            model_name='veranstaltung',
            name='digitale_eval',
            field=models.BooleanField(blank=True, default=False, help_text='Die Evaluation soll digital durchgeführt werden. Sie erhalten entsprechend viele TAN-Nummern auf Thermopapier, welche Sie an die Studiernden verteilen können. Die Studierenden füllen die Evaluation dann online aus.', verbose_name='Digitale Evaluation'),
        ),
    ]
