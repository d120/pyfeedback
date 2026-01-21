# coding=utf-8

from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_safe, require_http_methods
from feedback.views.public_class_view import barcodedrop
from feedback.models import Semester, get_model, Veranstaltung, Kommentar, EmailChange, Person
from feedback.forms import EMailChangeRequestForm, EMailChangeForm, EMailChangeValidateForm

from django.urls import reverse
from feedback import tools
from django.db import transaction
from django.contrib import messages
import uuid, logging
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

logger = logging.getLogger(__name__)


@require_safe
def index(request):
    data = {}
    data['thresh_show'] = settings.THRESH_SHOW
    data['thresh_valid'] = settings.THRESH_VALID

    # Zugangskontrolle
    if request.user.is_superuser or settings.DEBUG == True:
        authfilter = {}
    else:
        if not request.META['REMOTE_ADDR'].startswith('130.83.'):
            return render(request, 'public/unauth.html')
        authfilter = {'sichtbarkeit': 'ALL'}

    # Semesterliste laden
    data['semester_list'] = Semester.objects.filter(**authfilter).order_by('-semester')
    if not len(data['semester_list']):
        return render(request, 'public/keine_ergebnisse.html', data)

    # anzuzeigendes Semester auswählen
    try:
        data['semester'] = Semester.objects.get(semester=request.GET['semester'], **authfilter)
    except (KeyError, Semester.DoesNotExist):
        data['semester'] = data['semester_list'][0]

    # Ergebnisse einlesen
    Ergebnis = get_model('Ergebnis', data['semester'])
    ergebnisse = Ergebnis.objects.filter(veranstaltung__semester=data['semester'])

    # anzuzeigende Informationen auswählen
    if request.user.is_superuser or settings.DEBUG == True:
        data['parts'] = Ergebnis.parts + Ergebnis.hidden_parts
        data['include_hidden'] = True
    else:
        data['parts'] = Ergebnis.parts
        data['include_hidden'] = False

    # Sortierung
    try:
        parts = [part[0] for part in data['parts']]
        order = request.GET['order']
        if not order in parts:
            raise KeyError
        data['order'] = order
        data['order_num'] = parts.index(order) + 1
        data['ergebnisse'] = list(ergebnisse.order_by(order))

        # Veranstaltung mit zu kleinen Teilnehmerzahlen bei aktuellem Kriterium nach hinten sortieren
        tail = []
        for e in data['ergebnisse']:
            count = getattr(e, order + '_count')
            if count < settings.THRESH_SHOW:
                tail.append(e)

        for e in tail:
            data['ergebnisse'].remove(e)
        data['ergebnisse'].extend(tail)

    except KeyError:
        data['order'] = 'alpha'
        data['order_num'] = 0
        data['ergebnisse'] = list(ergebnisse.order_by('veranstaltung__name'))

    return render(request, 'public/index.html', data)


@require_safe
def veranstaltung(request, vid=None):
    # Zugangskontrolle
    if request.user.is_superuser or settings.DEBUG == True:
        authfilter = {}
    elif 'vid' in request.session and request.session['vid'] == int(vid):
        authfilter = {'semester__sichtbarkeit__in': ['ALL', 'VER']}
    else:
        if not request.META['REMOTE_ADDR'].startswith('130.83.'):
            return render(request, 'public/unauth.html')
        authfilter = {'semester__sichtbarkeit': 'ALL'}

    veranstaltung = get_object_or_404(Veranstaltung, id=vid, **authfilter)
    data = {'v': veranstaltung}
    if data['v'].semester.sichtbarkeit != 'ALL':
        data['restricted'] = True

    Ergebnis = get_model('Ergebnis', veranstaltung.semester)
    if veranstaltung.typ == 'v':
        parts = Ergebnis.parts_vl
    else:
        parts = Ergebnis.parts
    ergebnis = get_object_or_404(Ergebnis, veranstaltung=veranstaltung)
    data['parts'] = list(zip(parts, list(ergebnis.values())))
    data['ergebnis'] = ergebnis

    try:
        data['kommentar'] = Kommentar.objects.get(veranstaltung=veranstaltung)
    except Kommentar.DoesNotExist:
        pass

    return render(request, 'public/veranstaltung.html', data)


@require_http_methods(('HEAD', 'GET', 'POST'))
def email_change_request(request) :
    
    if request.method == 'POST':
        form = EMailChangeRequestForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                email_change = form.save(commit=False)

                email_change.token = uuid.uuid4()
                email_change.status = EmailChange.Status.MAGIC_LINK_SENT
                email_change.dynamic_expiry_time = timezone.now()
                email_change.save()

            person_exists = Person.objects.filter(email__iexact=email_change.old_email).exists()

            if person_exists:
                full_email_change_path = request.build_absolute_uri(
                    reverse("feedback:email-change", kwargs={"token": email_change.token})
                )

                try :
                    tools.send_change_email_link(
                        email_change.old_email,
                        full_email_change_path,
                        email_change.MINUTES_TO_EXPIRE_LINK,
                    )
                except Exception :
                    logger.exception(
                        _("Das Senden des E-Mail-Änderungslinks an %s ist fehlgeschlagen."),
                        email_change.old_email,
                    )

                    messages.warning(
                        request,
                        _("Beim Versenden der Bestätigungs-E-Mail ist ein Problem aufgetreten. Bitte versuchen Sie es später erneut.")
                    )
                    
                    return redirect("feedback:email-change-request")
            else:
                email_change.delete()


            return render(request, "public/email_change_send_confirmation.html", {"old_email": email_change.old_email})

    else:
        form = EMailChangeRequestForm()
    
    return render(request, "public/email_change_request.html", {"form": form})
        


@require_http_methods(("HEAD", "GET", "POST"))
def email_change(request, token=None):
    if token is None:
        return redirect("feedback:email-change-request")

    try: 
        email_change = get_object_or_404(
            EmailChange,
            token=token,
        )

        if not email_change.request_is_valid() :
            raise Exception("Link is no longer valid")
        
    except Exception :
        messages.error(request, _("Das Link ist nicht gültig."))
        return redirect("feedback:email-change-request")
    
    if not email_change.status == EmailChange.Status.MAGIC_LINK_SENT :
        if email_change.status == EmailChange.Status.OTP_SENT :
            return redirect("feedback:email-change-validate",token=email_change.token)
        else :
            messages.error(request, _("Das Link ist nicht gültig."))
            return redirect("feedback:email-change-request")


    if request.method == "POST":
        form = EMailChangeForm(request.POST, instance=email_change)

        if form.is_valid():
            email_change = form.save(commit=False)

            otp, hash = email_change.generate_otp_and_hash()

            email_change.status = EmailChange.Status.OTP_SENT
            email_change.dynamic_expiry_time = timezone.now()
            email_change.new_email_otp_hash = hash
            email_change.save()
            form.save_m2m()

            tools.send_change_email_otp(email_change.new_email, email_change.old_email, otp, email_change.MINUTES_TO_EXPIRE_OTP,)

            return redirect("feedback:email-change-validate", token=email_change.token)

    else:
        form = EMailChangeForm(instance=email_change)

    return render(request, "public/email_change.html", {"form": form})


@require_http_methods(("HEAD", "GET", "POST"))
def email_change_validate(request, token=None):
    if token is None:
        return redirect("feedback:email-change-request")

    try: 
        email_change = get_object_or_404(
            EmailChange,
            token=token,
        )

        if not email_change.request_is_valid() :
            raise Exception("Request is no longer valid")
        
    
    except Exception :
        messages.error(request, _("Das Link ist nicht mehr gültig."))
        return redirect("feedback:email-change-request")
    
    if not email_change.status == EmailChange.Status.OTP_SENT :
        if email_change.status == EmailChange.Status.MAGIC_LINK_SENT :
            messages.error(request, _("Sie müssen eine neue E-Mail eingeben."))
            return redirect("feedback:email-change",token=email_change.token)
        else :
            messages.error(request, _("Das Link ist nicht gültig."))
            return redirect("feedback:email-change-request")


    if request.method == "POST":
        form = EMailChangeValidateForm(request.POST, instance=email_change)

        if form.is_valid():
            with transaction.atomic():
                email_change.person_list_to_change.update(
                    email=email_change.new_email
                )

                email_change.status = EmailChange.Status.COMPLETED
                email_change.new_email_otp_hash = ""
                email_change.save(
                    update_fields=[
                        "status",
                        "new_email_otp_hash",
                    ]
                )

            return render(request, "public/email_change_complete.html", {"new_email": email_change.new_email,})
        
    else:
        form = EMailChangeValidateForm(instance=email_change)

    return render(request, "public/email_change_validate.html", {"form": form})

