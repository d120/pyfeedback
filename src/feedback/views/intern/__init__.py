# coding=utf-8
import ast
import os
import subprocess

from io import TextIOWrapper
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mass_mail, EmailMessage
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import smart_str
from django.views.decorators.http import require_safe, require_http_methods
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import FormView
from formtools.wizard.views import SessionWizardView
from django.core.files.storage import default_storage
from django import forms
from django.core import mail

from feedback import tools
from feedback.forms import CloseOrderForm
from feedback.forms import UploadFileForm
from feedback.forms import UploadTANCSV, SendOrPDF, EMailTemplates
from feedback.parser.ergebnisse import parse_ergebnisse
from feedback.views import public
from feedback.models import Veranstaltung, Semester, Einstellung, Mailvorlage, get_model, long_not_ordert, \
    FachgebietEmail, Tutor 
from feedback.models.fragebogenUE2016 import FragebogenUE2016
import feedback.parser.tan as tanparser



@user_passes_test(lambda u: u.is_superuser)
@require_safe
def index(request):
    cur_semester = Semester.current()
    all_veranst = Veranstaltung.objects.filter(semester=cur_semester)

    # Veranstaltung für die es Rückmeldungen gibt
    ruck_veranst = all_veranst.filter(status__gte=Veranstaltung.STATUS_KEINE_EVALUATION, semester=cur_semester)

    num_all_veranst = all_veranst.count()
    num_ruck_veranst = ruck_veranst.count()

    relativ_result = 0

    if num_all_veranst >= 1:
        relativ_result = (100/float(num_all_veranst)) * num_ruck_veranst

    width_progressbar = 500
    width_progressbar_success = int(float(width_progressbar)/100 * relativ_result)

    return render(request, 'intern/index.html', {'cur_semester': cur_semester,
                                                 'all_veranst': num_all_veranst,
                                                 'ruck_veranst': num_ruck_veranst,
                                                 'relativ_result': relativ_result,
                                                 'width_progressbar': width_progressbar,
                                                 'width_progressbar_success': width_progressbar_success,})


@user_passes_test(lambda u: u.is_superuser)
@require_safe
def lange_ohne_evaluation(request):
    return render(request, 'intern/lange_ohne_evaluation.html', {'veranstaltungen': long_not_ordert()})


@user_passes_test(lambda u: u.is_superuser)
@require_safe
def fragebogensprache(request):
    veranstaltungen = Veranstaltung.objects.filter(semester=Semester.current())
    veranstaltungen = veranstaltungen.filter(anzahl__gt=0, evaluieren=True, status__gte=Veranstaltung.STATUS_BESTELLUNG_WIRD_VERARBEITET)
    veranstaltungen = veranstaltungen.order_by('sprache','typ','anzahl')

    data = {'veranstaltungen': veranstaltungen}
    return render(request, 'intern/fragebogensprache.html', data)


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def export_veranstaltungen(request):
    if request.method in ('HEAD', 'GET'):
        data = {'semester': Semester.objects.order_by('-semester')}
        return render(request, 'intern/export_veranstaltungen.html', data)

    # POST request
    try:
        semester = Semester.objects.get(semester=request.POST['semester'])
    except (Semester.DoesNotExist, KeyError):
        return HttpResponseRedirect(reverse('export_veranstaltungen'))

    ubung_export = False
    if request.POST.get("xml_ubung", None) is not None:
        ubung_export = True

    if ubung_export:
        # nur Übungen
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True,
                                               anzahl__gt=0, typ='vu').select_related('verantwortlich')
    else:
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True,
                                               anzahl__gt=0).select_related('verantwortlich')

    if not veranst.count():
        if ubung_export:
            messages.error(request, 'Für das ausgewählte Semester (%s) liegen keine Bestellungen '
                                    'für Vorlesungen mit Übung vor!' % semester)
        else:
            messages.error(request, 'Für das ausgewählte Semester (%s) liegen keine Bestellungen vor!' % semester)
        return HttpResponseRedirect(reverse('export_veranstaltungen'))

    missing_verantwortlich = veranst.filter(verantwortlich=None)
    if missing_verantwortlich.count() > 0:
        txt = ', '.join([v.name for v in missing_verantwortlich])
        messages.error(request, 'Für die folgenden Veranstaltungen ist kein Verantwortlicher eingetragen: %s' % txt)
        return HttpResponseRedirect(reverse('export_veranstaltungen'))

    missing_sprache = veranst.filter(sprache=None)
    if missing_sprache.count() > 0:
        txt = ', '.join([v.name for v in missing_sprache])
        messages.error(request, 'Für die folgenden Veranstaltungen ist keine Sprache eingetragen: %s' % txt)
        return HttpResponseRedirect(reverse('export_veranstaltungen'))

    person_set = set()

    data = {
        'veranst': veranst,
        'ubung_export': ubung_export
    }

    for ver in veranst:
        for cur_empf in ver.ergebnis_empfaenger.all():
            person_set.add(cur_empf)

    data['person'] = list(person_set)

    xml_out = render(request, 'intern/evasys-export.xml', data)

    response = HttpResponse(xml_out, content_type='application/xml')

    filename = "veranstaltungen"
    if ubung_export:
        filename = "ubung"

    response['Content-Disposition'] = 'attachment; filename="' + filename + '.xml"'

    return response


def translate_to_latex(text):
    dic = {
        '&': '\&',
        '%': '\%',
        '$': '\$',
        '#': '\#',
        '_': '\_',
        '"': '"{}',
        '~': '\~{}',
        '^': '\\textasciicircum',
    }
    for i, j in dic.items():
            text = text.replace(i, j)
    return text


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def generate_letters(request):
    data = {
        'semester': Semester.objects.all()
    }

    datefilename = settings.LATEX_PATH + 'erhebungswoche.inc'

    # Wenn die Datei noch nicht vorhanden ist erzeuge sie
    if not(os.path.exists(datefilename)):
        with open(datefilename, 'w') as f:
            f.write('')

    if request.method in ('HEAD', 'GET'):
        with open(datefilename, 'r') as f:
            data['erhebungswoche'] = f.readline()
        return render(request, 'intern/generate_letters.html', data)

    try:
        semester = Semester.objects.get(semester=request.POST['semester'])
    except (Semester.DoesNotExist, KeyError):
        return HttpResponseRedirect(reverse('generate_letters'))

    try:
        vorlage = request.POST['vorlage']
    except (Semester.DoesNotExist, KeyError):
        return HttpResponseRedirect(reverse('generate_letters'))

    if vorlage == 'Anschreiben':
        latexpath = settings.LATEX_PATH
        templatename = 'anschreiben'
    elif vorlage == 'Aufkleber':
        latexpath = settings.LATEX_PATH+'../aufkleber/'
        templatename = 'aufkleber'

    # aus Sicherheitsgründen TeX-Befehle in Abgabedatum-String deaktivieren
    # TODO: Kalender-Widget einführen, nur noch dessen Format akzeptieren
    try:
        abgabedatum = request.POST['erhebungswoche'].replace('\\', '')
    except KeyError:
        return HttpResponseRedirect(reverse('generate_letters'))
    with open(datefilename, 'w') as f:
        f.write(abgabedatum)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s.pdf' % (templatename)

    if vorlage != 'Aufkleber':
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True, anzahl__gt=0).order_by('sprache','anzahl')
    elif 'anzahlaufkleber' in request.POST and request.POST['anzahlaufkleber'].isdigit():
        anzahl = request.POST['anzahlaufkleber']
        anzahl = int(anzahl)
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True, anzahl__gte=anzahl).order_by('name')
    else:
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True, anzahl__gt=0).order_by('name')

    if not veranst.count():
        messages.error(request, 'Für das ausgewählte Semester (%s) liegen '
                                'keine Bestellungen vor oder die Mindesteilnehmeranzahl ist zu hoch!' % semester)
        return HttpResponseRedirect(reverse('generate_letters'))

    lines = []
    for v in veranst:
        eva_id=v.get_barcode_number()
        empfaenger = str(v.verantwortlich.full_name())
        line = '\\adrentry{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}\n' % (
                        translate_to_latex(v.verantwortlich.full_name()), translate_to_latex(v.verantwortlich.anschrift), translate_to_latex(v.name), v.anzahl, v.sprache, v.get_typ_display(), eva_id, v.freiefrage1.strip(), v.freiefrage2.strip())
        lines.append(smart_str(line))

    # TODO: prüfen, ob nötige Dateien schreibbar sind (abgabedatum.inc, anschreiben.{log,aux,pdf}, veranstalter.adr)

    with open(latexpath + 'veranstalter.adr', 'w') as f:
        f.writelines(lines)

    # keine Ausgaben auf die Konsole schreiben (sichtbar z.B. beim Testen)
    with open(os.devnull, 'w') as devnull:
        # PDF via LaTeX erzeugen
        ret = subprocess.call(['/usr/bin/pdflatex', '-interaction', 'batchmode', '-halt-on-error',
                               templatename+'.tex'], cwd=latexpath, stdout=devnull, stderr=devnull)

    if ret or hasattr(settings, 'TEST_LATEX_ERROR'):
        with open(latexpath + templatename + '.log', 'r') as f:
            data['texlog'] = f.read()
        return render(request, 'intern/generate_letters.html', data)

    with open(latexpath + templatename + '.pdf', 'rb') as f:
        response.write(f.read())
    return response


def get_relevant_veranstaltungen(chosen_status_list, semester):
    """
    Gibt die relevanten Veranstaltungen für die ausgewählten Status zurück.
    :param chosen_status_list: List
    :param semester: Semester
    :return: List
    """
    veranstaltungen = []
    for status in chosen_status_list:
        if status == 0:
            for veranstaltung in Veranstaltung.objects.filter(semester=semester):
                veranstaltungen.append(veranstaltung)
        else:
            for veranstaltung in Veranstaltung.objects.filter(semester=semester, status=status):
                veranstaltungen.append(veranstaltung)
    return veranstaltungen


def process_status_post_data_from(post_list):
    """
    Da Django POST Daten in Unicode wrapped, casten wir die Statuscodes aus dem POST-Request zu Integers.
    :param post_list: List
    :return: List
    """
    processed_data = []
    for data in post_list:
        processed_data.append(int(data))
    return processed_data


def get_demo_context(request):
    """
    Setzt ein paar Variablen, die für einen Demo Context gebraucht werden.
    :param request: POST
    :return: RequestContext, String, String
    """
    color_span = '<span style="color:blue">{}</span>'
    link_veranstalter = 'https://www.fachschaft.informatik.tu-darmstadt.de%s' % reverse('veranstalter-login')
    link_suffix_format = '?vid=%d&token=%s'
    demo_context = RequestContext(request, {
        'veranstaltung': color_span.format('Grundlagen der Agrarphilosophie I'),
        'link_veranstalter': color_span.format(link_veranstalter + (link_suffix_format % (1337, '0123456789abcdef'))),
    })
    return demo_context, link_suffix_format, link_veranstalter


def set_up_choices():
    """
    Setzt die Auswahlmöglichkeiten für die View.
    :return: List, List
    """
    tutoren_choices = [(False, 'Nein'), (True, 'Ja')]
    status_choices = [(0, 'Alle Veranstaltungen')]
    for choice_key, choice in Veranstaltung.STATUS_CHOICES:
        status_choices.append((choice_key, choice))
    return status_choices, tutoren_choices


def add_sekretaerin_mail(recipients, veranstaltung):
    """
    Fügt die E-Mail Adresse der Sekretärin in die Empfängerlist hinzu.
    :param recipients: List
    :param veranstaltung: Veranstaltung
    """
    for person in veranstaltung.veranstalter.all():
        fachgebiet = person.fachgebiet
        if fachgebiet is not None:
            mails = FachgebietEmail.objects.filter(fachgebiet=fachgebiet)
            for mail in mails:
                if (mail.email_sekretaerin is not None) and (mail.email_sekretaerin not in recipients):
                    recipients.append(mail.email_sekretaerin)


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def sendmail(request):
    """Die View-Funktion für den Mailversand."""
    data = {
        'semester': Semester.objects.order_by('-semester'),
        'vorlagen': Mailvorlage.objects.all(),
    }

    status_choices, tutoren_choices = set_up_choices()
    data['veranstaltung_status_choices'] = status_choices
    data['tutoren_choices'] = tutoren_choices

    if request.method == 'POST':
        
        try:
            semester = Semester.objects.get(semester=request.POST['semester'])
            data['subject'] = request.POST['subject']
            data['body'] = request.POST['body']
            data['tutoren'] = request.POST['tutoren']

            if 'recipient' in request.POST.keys():
                data['recipient'] = process_status_post_data_from(request.POST.getlist('recipient'))
                data['recipient_selected'] = data['recipient']
            elif 'status_values' in request.POST.keys():
                data['recipient'] = ast.literal_eval(request.POST.get('status_values'))
            elif 'uebernehmen' not in request.POST:
                return HttpResponseRedirect(reverse('sendmail'))

        except (Semester.DoesNotExist, KeyError):
            return HttpResponseRedirect(reverse('sendmail'))

        data['semester_selected'] = semester
        data['subject_rendered'] = "Evaluation: %s" % data['subject']
        
        if 'uebernehmen' in request.POST:
            try:
                vorlage = Mailvorlage.objects.get(id=int(request.POST['vorlage']))
                data['subject'] = vorlage.subject
                data['body'] = vorlage.body
       
            except (Mailvorlage.DoesNotExist, KeyError, ValueError):
                return HttpResponseRedirect(reverse('sendmail'))
            return render(request, 'intern/sendmail.html', data)

        veranstaltungen = get_relevant_veranstaltungen(data['recipient'], semester)
        demo_context, link_suffix_format, link_veranstalter = get_demo_context(request)

        
        if 'vorschau' in request.POST:
            data['vorschau'] = True
            data['from'] = settings.DEFAULT_FROM_EMAIL
            data['to'] = "Veranstalter von %d Veranstaltungen" % len(veranstaltungen)
            data['is_tutoren'] = "und den Tutoren dieser Veranstaltungen"
            data['body_rendered'] = tools.render_email(data['body'], demo_context)

            for status in data['recipient']:
                if status <= Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR:
                    if Einstellung.get('bestellung_erlaubt') == '0':
                        messages.warning(request,
                                         'Bestellungen sind aktuell nicht erlaubt! Bist du ' +
                                         'sicher, dass du trotzdem die Dozenten anschreiben willst, ' +
                                         'die noch nicht bestellt haben?')
                elif status == Veranstaltung.STATUS_ERGEBNISSE_VERSANDT:
                    if semester.sichtbarkeit != 'VER':
                        messages.warning(request,
                                         'Die Sichtbarkeit der Ergebnisse des ausgewählten ' +
                                         'Semesters ist aktuell nicht auf "Veranstalter" ' +
                                         'eingestellt! Bist du sicher, dass du trotzdem die ' +
                                         'Dozenten anschreiben willst, für deren Veranstaltungen '
                                         'Ergebnisse vorliegen?')

            return render(request, 'intern/sendmail_preview.html', data)

        elif 'senden' in request.POST:
            mails = []

            # Mails für die Veranstaltungen
            for v in veranstaltungen:
                subject = data['subject']
                context = RequestContext(request, {
                    'veranstaltung': v.name,
                    'link_veranstalter': link_veranstalter + (link_suffix_format % (v.id, v.access_token)),
                })
                body = tools.render_email(data['body'], context)
                recipients = [person.email for person in v.veranstalter.all() if person.email]

                if data['tutoren'] == 'True':
                    emails = Tutor.objects.filter(veranstaltung=v).values('email')
                    for dic in emails:
                        recipients.append(dic['email'])
                else:
                    add_sekretaerin_mail(recipients, v)

                if not recipients:
                    messages.warning(request,
                                     ('An die Veranstalter von "%s" wurde keine Mail ' +
                                      'verschickt, da keine Adressen hinterlegt waren.') % v.name)
                    continue

                mails.append((subject, body, settings.DEFAULT_FROM_EMAIL, recipients))

            # Kopie für das Feedback-Team
            subject = data['subject_rendered']
            body = tools.render_email(data['body'], demo_context)
            mails.append((subject, body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL]))

            # Mails senden
            send_mass_mail(mails)

            if data['tutoren'] == 'True':
                messages.success(request,
                                 '%d Veranstaltungen wurden erfolgreich, samt Tutoren, benachrichtigt.' % (len(mails)-1))
            else:
                messages.success(request, '%d Veranstaltungen wurden erfolgreich benachrichtigt.' % (len(mails) - 1))
            return HttpResponseRedirect(reverse('intern-index'))

    return render(request, 'intern/sendmail.html', data)


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def import_ergebnisse(request):
    data = {}

    if request.method == 'POST':
        try:
            semester = Semester.objects.get(semester=request.POST['semester'])
        except (Semester.DoesNotExist, KeyError):
            return HttpResponseRedirect(reverse('import_ergebnisse'))

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if 'typ' in request.POST and request.POST['typ'] == 'uebung':
                warnings, errors, vcount, fbcount = parse_ergebnisse(semester, TextIOWrapper(request.FILES['file'].file, encoding='ISO-8859-1'), 'UE2016')
            else:
                warnings, errors, vcount, fbcount = parse_ergebnisse(semester, TextIOWrapper(request.FILES['file'].file, encoding='ISO-8859-1'))
            if fbcount:
                messages.success(request,
                    '%u Veranstaltungen mit insgesamt %u Fragebögen wurden erfolgreich importiert.' %
                    (vcount, fbcount))
            else:
                warnings.append('Es konnten keine Fragebögen importiert werden.')

            for w in warnings:
                messages.warning(request, w)
            for e in errors:
                messages.error(request, e)
            return HttpResponseRedirect(reverse('sync_ergebnisse'))
        else:
            messages.error(request, 'Fehler beim Upload')
    else:
        data['semester'] = Semester.objects.all()
        data['form'] = UploadFileForm()

    return render(request, 'intern/import_ergebnisse.html', data)


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def sync_ergebnisse(request):
    if request.method in ('HEAD', 'GET'):
        data = {'semester': Semester.objects.all()}
        return render(request, 'intern/sync_ergebnisse.html', data)

    try:
        semester = Semester.objects.get(semester=request.POST['semester'])
    except (Semester.DoesNotExist, KeyError):
        return HttpResponseRedirect(reverse('sync_ergebnisse'))

    fragebogen = get_model('Fragebogen', semester)
    ergebnis = get_model('Ergebnis', semester)
    ergebnis.objects.filter(veranstaltung__semester=semester).delete()

    found_something = False
    if semester.fragebogen == '2016':
        for v in Veranstaltung.objects.filter(semester=semester):
            fbs = fragebogen.objects.filter(veranstaltung=v)
            erg = FragebogenUE2016.objects.filter(veranstaltung=v)
            if len(fbs):
                found_something = True
                data = {'veranstaltung': v, 'anzahl': len(fbs)}
                for part in ergebnis.parts + ergebnis.hidden_parts:
                    result, count = tools.get_average(ergebnis, fbs, part[0])
                    data[part[0]] = result
                    data[part[0]+'_count'] = count
                for part in ergebnis.parts_ue:
                    result, count = tools.get_average(ergebnis, erg, part[0])
                    data[part[0]] = result
                    data[part[0]+'_count'] = count
                ergebnis.objects.create(**data)

    else:
        for v in Veranstaltung.objects.filter(semester=semester):
            fbs = fragebogen.objects.filter(veranstaltung=v)
            if len(fbs):
                found_something = True
                data = {'veranstaltung': v, 'anzahl': len(fbs)}
                for part in ergebnis.parts + ergebnis.hidden_parts:
                    result, count = tools.get_average(ergebnis, fbs, part[0])
                    data[part[0]] = result
                    data[part[0]+'_count'] = count
                ergebnis.objects.create(**data)

    if not found_something:
        messages.warning(request, 'Für das %s liegen keine Ergebnisse vor.' % semester)
    else:
        messages.success(request, 'Das Ranking für das %s wurde erfolgreich berechnet.' % semester)
    return HttpResponseRedirect(reverse('sync_ergebnisse'))


@user_passes_test(lambda u: u.is_superuser)
def ergebnisse(request):
    return public.index(request)


def is_no_evaluation_final(status):
    return status == Veranstaltung.STATUS_KEINE_EVALUATION or status == Veranstaltung.STATUS_ANGELEGT or \
           status == Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET


def update_veranstaltungen_status(veranstaltungen):
    for v in veranstaltungen:
        if is_no_evaluation_final(v.status):
            v.status = Veranstaltung.STATUS_KEINE_EVALUATION_FINAL
            v.save()
        elif v.status == Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR:
            v.status = Veranstaltung.STATUS_BESTELLUNG_WIRD_VERARBEITET
            v.save()


class CloseOrderFormView(UserPassesTestMixin, FormView):
    """Definiert die View für das Beenden der Bestellphase."""
    template_name = 'intern/status_final.html'
    form_class = CloseOrderForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid:
            choice = self.get_form_kwargs().get('data').get('auswahl')
            if choice == 'ja':
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def form_valid(self, form):
        update_veranstaltungen_status(self.get_queryset())
        messages.success(self.request, 'Alle Status wurden erfolgreich aktualisiert.')
        return super(CloseOrderFormView, self).form_valid(form)

    def form_invalid(self, form):
        return HttpResponseRedirect(reverse('intern-index'))

    def get_queryset(self):
        try:
            veranstaltungen = Veranstaltung.objects.filter(semester=Semester.current())
            return veranstaltungen
        except (Veranstaltung.DoesNotExist, KeyError):
            messages.warning(self.request, 'Keine passenden Veranstaltungen für das aktuelle Semester gefunden.')
            return HttpResponseRedirect(reverse('intern-index'))

    def get_success_url(self):
        return reverse('intern-index')

    def test_func(self):
        return self.request.user.is_superuser

class ProcessTANs(UserPassesTestMixin, SessionWizardView):
    template_name = 'intern/tans/process_tans.html'
    form_list = [UploadTANCSV, SendOrPDF, EMailTemplates, forms.Form]
    file_storage = default_storage

    def done(self, form_list, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        # parse csv
        tans = tanparser.parse(form_data[0]['csv'])
        # send mass mail for losungs people
        cur_semester = Semester.current()
        lectures = Veranstaltung.objects.filter(semester=cur_semester,  digitale_eval=True,status__gte=Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR).prefetch_related('veranstalter')

        mails = []
        losungtemplate = form_data[2]['losungstemplate'].body
        for lecture in lectures.filter(digitale_eval_type='L'):
            subject = 'Losung für die Veranstaltung {}'.format(lecture.name)
            context = RequestContext(self.request, {
                    'veranstaltung': lecture.name,
                    'losung': tans[lecture.name][0],
            })
            body = tools.render_email(losungtemplate, context)
            recipients = [person.email for person in lecture.veranstalter.all() if person.email]
            email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, recipients)
            mails.append(email)

        # send massmail for tan people
        losungtemplate = form_data[2]['tantemplate'].body
        for lecture in lectures.filter(digitale_eval_type='T'):
            subject = 'TANs für die Veranstaltung {}'.format(lecture.name)
            context = RequestContext(self.request, {
                    'veranstaltung': lecture.name,
            })
            body = tools.render_email(losungtemplate, context)
            recipients = [person.email for person in lecture.veranstalter.all() if person.email]
            email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, recipients)
            tancsv = 'TANS,\n' + '; \n'.join(tans[lecture.name])
            email.attach('tans.csv', tancsv, 'text/csv')
            mails.append(email)

        mail_connection = mail.get_connection()
        mail_connection.send_messages(mails)
        messages.success(self.request,
                                 '{} Veranstaltungen wurden erfolgreich benachrichtigt.'.format(len(mails)))
        return HttpResponseRedirect(reverse('intern-index'))

    def get_template_names(self):
        return [self.template_name] if self.steps.step0 != 3 else ['intern/tans/process_tans_preview.html']

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.step0 == 3:
            form_data = self.get_all_cleaned_data()
            demo_context, _, _ = get_demo_context(self.request)
            context['tanpreview'] = tools.render_email(form_data['tantemplate'].    body, demo_context)
            demo_context['losung'] = '<span style="color:blue">LOSUNGLOSUNG</span>'
            context['losungspreview'] = tools.render_email(form_data   ['losungstemplate'].body, demo_context)
            cur_semester = Semester.current()
            lectures = Veranstaltung.objects.filter(semester=cur_semester,  digitale_eval=True)
            context['tanlectures'] = list(lectures.filter(digitale_eval_type='T'). values_list('name', flat=True))
            context['losunglectures'] = list(lectures.filter(digitale_eval_type='L').  values_list('name', flat=True))
        return context  

    def test_func(self):
        return self.request.user.is_superuser