# coding=utf-8

from django.template import TemplateSyntaxError, Template

from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from django.conf import settings

# ------------------------------ Durchschnittsberechnung für das Ranking ------------------------------ #

def get_average(ergebnis, fb_list, attr):
    """Berechnet das gewichtete Mittel über das Attribut attr für die Fragebogenliste fb_list."""

    # alle Ergebnisse, die in Mittelwert einfließen, zusammenstellen
    try:
        parts = getattr(ergebnis, attr + '_parts')
    except AttributeError:
        parts = [attr]

    # Gewichte einlesen, falls Bestandteile nicht zu gleichen Teilen in den Mittelwert eingehen sollen
    if attr in ergebnis.weight:
        weights = ergebnis.weight[attr]
    else:
        weights = [1] * len(parts)

    # Anzahl an Fragebögen, die ins Ergebnis eingehen
    fb_count = 0

    # gewichtete Zahl der Werte, die in das Ergebnis eingeht
    weighted_count = 0

    # gewichtete Werte, die in das Ergebnis eingehen
    weighted_sum = 0

    for fb in fb_list:
        contains_valid_field = False

        for part, weight in zip(parts, weights):
            value = getattr(fb, part)
            # Evasys gibt auch den Wert int(0) zurück
            # siehe: https://www.fachschaft.informatik.tu-darmstadt.de/trac/fs/ticket/1192
            if value is not None and value >= 1:
                contains_valid_field = True
                weighted_count += weight
                weighted_sum += value * weight

        if contains_valid_field:
            fb_count += 1

    if fb_count > 0:
        average = weighted_sum / float(weighted_count)
        return average, fb_count
    else:
        return None, 0


### Durchschnittsberechnung für das Ranking ###################################

def get_average_16(ergebnis, fb_list, erg_list, attr):
    """Berechnet das gewichtete Mittel über das Attribut attr für die Fragebogenliste fb_list."""

    # alle Ergebnisse, die in Mittelwert einfließen, zusammenstellen
    try:
        parts = getattr(ergebnis, attr + '_parts')
    except AttributeError:
        parts = [attr]

    # Gewichte einlesen, falls Bestandteile nicht zu gleichen Teilen in den Mittelwert eingehen sollen
    if attr in ergebnis.weight:
        weights = ergebnis.weight[attr]
    else:
        weights = [1] * len(parts)

    # Anzahl an Fragebögen, die ins Ergebnis eingehen
    fb_count = 0

    # gewichtete Zahl der Werte, die in das Ergebnis eingeht
    weighted_count = 0

    # gewichtete Werte, die in das Ergebnis eingehen
    weighted_sum = 0

    for fb in fb_list:
        contains_valid_field = False

        for part, weight in zip(parts, weights):
            value = getattr(fb, part)
            # Evasys gibt auch den Wert int(0) zurück
            # siehe: https://www.fachschaft.informatik.tu-darmstadt.de/trac/fs/ticket/1192
            if value is not None and value >= 1:
                contains_valid_field = True
                weighted_count += weight
                weighted_sum += value * weight

        if contains_valid_field:
            fb_count += 1

    if fb_count > 0:
        average = weighted_sum / float(weighted_count)
        return average, fb_count

    else:
        return None, 0
# ------------------------------ E-Mail-Handling ------------------------------ #

def render_email(template, context):
    try:
        return Template('{% autoescape off %}' + template + '{% endautoescape %}').render(context)
    except TemplateSyntaxError:
        return "!!! Syntaxfehler im Mailtext !!!"


def ean_checksum_calc(number):
    """ Berechne die Checksumme eines EAN Barcodes"""
    offset = 0

    # convert a int to a list of ints
    x = [int(i) for i in str(number)]
    length = len(x)
    if length == 8 or length == 13:
        offset = 1

    # nehme jedes 2 element beginned beim letzten element und gehe nach vorne zum ersten element,
    return (-(sum(x[-(1 + offset)::-2]) * 3 + sum(x[-(2 + offset)::-2]))) % 10


def ean_checksum_valid(x):
    """ Prüfe die Checksumme eines EAN Barcodes"""
    length = len(str(x))
    result = False
    if length == 8 or length == 13:
        if x % 10 == ean_checksum_calc(x):
            result = True
    return result

def send_change_email_link(to_email, link, minutes_to_expire) :
    """
    sends mail to given email with given link as a part of email change process
    """
    subject = _("E-Mail-Änderungsanfrage")

    message = render_to_string(
        "emails/email_change.txt",
        {"email": to_email, "link": mark_safe(link), "minutes_to_expire": minutes_to_expire,}
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )

def send_change_email_otp(to_email, old_email, otp, minutes_to_expire) :
    """
    sends mail with otp
    """
    subject = _("E-Mail-Änderungsanfrage OTP")

    message = render_to_string(
        "emails/email_change_otp.txt",
        {"email": to_email, "old_email": old_email, "otp": mark_safe(otp), "minutes_to_expire": minutes_to_expire,}
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


