# coding=utf-8
import ast
import os
import subprocess

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import smart_str
from django.views.decorators.http import require_safe, require_http_methods

from feedback import tools
from feedback.forms import UploadFileForm
from feedback.models import Veranstaltung, Semester, Einstellung, Mailvorlage, get_model, long_not_ordert, FachgebietEmail
from feedback.parser.ergebnisse import parse_ergebnisse
from feedback.views import public


@user_passes_test(lambda u: u.is_superuser)
@require_safe
def index(request):
    cur_semester = Semester.current()
    all_veranst = Veranstaltung.objects.filter(semester=cur_semester)

    # Veranstaltung für die es Rückmeldungen gibt
    ruck_veranst = all_veranst.filter(Q(anzahl__gt=0) | Q(evaluieren=False))

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
    veranstaltungen = veranstaltungen.filter(anzahl__gt=0, evaluieren=True)
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
            messages.error(request, u'Für das ausgewählte Semester (%s) liegen keine Bestellungen '
                                    u'für Vorlesungen mit Übung vor!' % semester)
        else:
            messages.error(request, u'Für das ausgewählte Semester (%s) liegen keine Bestellungen vor!' % semester)
        return HttpResponseRedirect(reverse('export_veranstaltungen'))

    missing_verantwortlich = veranst.filter(verantwortlich=None)
    if missing_verantwortlich.count() > 0:
        txt = ', '.join([v.name for v in missing_verantwortlich])
        messages.error(request, u'Für die folgenden Veranstaltungen ist kein Verantwortlicher eingetragen: %s' % txt)
        return HttpResponseRedirect(reverse('export_veranstaltungen'))

    missing_sprache = veranst.filter(sprache=None)
    if missing_sprache.count() > 0:
        txt = ', '.join([v.name for v in missing_sprache])
        messages.error(request, u'Für die folgenden Veranstaltungen ist keine Sprache eingetragen: %s' % txt)
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
    for i, j in dic.iteritems():
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
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True, anzahl__gt=anzahl).order_by('sprache','anzahl')
    else:
        veranst = Veranstaltung.objects.filter(semester=semester, evaluieren=True, anzahl__gt=0).order_by('sprache', 'anzahl')

    if not veranst.count():
        messages.error(request, 'Für das ausgewählte Semester (%s) liegen '
                                'keine Bestellungen vor oder die Mindesteilnehmeranzahl ist zu hoch!' % semester)
        return HttpResponseRedirect(reverse('generate_letters'))

    lines = []
    for v in veranst:
        eva_id=v.get_barcode_number()
        empfaenger = unicode(v.verantwortlich.full_name())
        line = u'\\adrentry{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}\n' % (
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

    with open(latexpath + templatename + '.pdf', 'r') as f:
        response.write(f.read())
    return response


def get_relevant_veranstaltungen(chosen_status_list, semester):
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
    processed_data = []
    for data in post_list:
        processed_data.append(int(data))
    return processed_data


def get_demo_context(request):
    color_span = '<span style="color:blue">{}</span>'
    link_veranstalter = 'https://www.fachschaft.informatik.tu-darmstadt.de%s' % reverse('veranstalter-login')
    link_suffix_format = '?vid=%d&token=%s'
    demo_context = RequestContext(request, {
        'veranstaltung': color_span.format('Grundlagen der Agrarphilosophie I'),
        'link_veranstalter': color_span.format(link_veranstalter + (link_suffix_format % (1337, '0123456789abcdef'))),
    })
    return demo_context, link_suffix_format, link_veranstalter


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def sendmail(request):
    data = {
        'semester': Semester.objects.order_by('-semester'),
        'vorlagen': Mailvorlage.objects.all(),
    }

    status_choises = [(0, 'Alle Veranstaltungen')]
    for choise_key, choise in Veranstaltung.STATUS_CHOICES:
        status_choises.append((choise_key, choise))

    data["veranstaltung_status_choises"] = status_choises

    if request.method == 'POST':
        try:
            semester = Semester.objects.get(semester=request.POST['semester'])
            data['subject'] = request.POST['subject']
            data['body'] = request.POST['body']

            if 'recipient' in request.POST.keys():
                data['recipient'] = process_status_post_data_from(request.POST.getlist('recipient'))
            elif 'status_values' in request.POST.keys():
                data['recipient'] = ast.literal_eval(request.POST.get('status_values'))

        except (Semester.DoesNotExist, KeyError):
            return HttpResponseRedirect(reverse('sendmail'))

        data['semester_selected'] = semester
        data['subject_rendered'] = "Evaluation: %s" % data['subject']

        veranstaltungen = get_relevant_veranstaltungen(data['recipient'], semester)
        demo_context, link_suffix_format, link_veranstalter = get_demo_context(request)

        if 'uebernehmen' in request.POST:
            try:
                vorlage = Mailvorlage.objects.get(id=int(request.POST['vorlage']))
                data['subject'] = vorlage.subject
                data['body'] = vorlage.body
            except (Mailvorlage.DoesNotExist, KeyError, ValueError):
                return HttpResponseRedirect(reverse('sendmail'))

        elif 'vorschau' in request.POST:
            data['vorschau'] = True
            data['from'] = settings.DEFAULT_FROM_EMAIL
            data['to'] = "Veranstalter von %d Veranstaltungen" % len(veranstaltungen)
            data['body_rendered'] = tools.render_email(data['body'], demo_context)

            for status in data['recipient']:
                if status <= Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR:
                    if Einstellung.get('bestellung_erlaubt') == '0':
                        messages.warning(request,
                                         u'Bestellungen sind aktuell nicht erlaubt! Bist du ' +
                                         u'sicher, dass du trotzdem die Dozenten anschreiben willst, ' +
                                         u'die noch nicht bestellt haben?')
                elif status == Veranstaltung.STATUS_ERGEBNISSE_VERSANDT:
                    if semester.sichtbarkeit != 'VER':
                        messages.warning(request,
                                         u'Die Sichtbarkeit der Ergebnisse des ausgewählten ' +
                                         u'Semesters ist aktuell nicht auf "Veranstalter" ' +
                                         u'eingestellt! Bist du sicher, dass du trotzdem die ' +
                                         u'Dozenten anschreiben willst, für deren Veranstaltungen '
                                         u'Ergebnisse vorliegen?')

            return render(request, 'intern/sendmail_preview.html', data)

        elif 'senden' in request.POST:
            mails = []

            # Mails für die Veranstaltungen
            print "VERANSTALTUNGEN ===> ", veranstaltungen
            for v in veranstaltungen:
                subject = data['subject']
                context = RequestContext(request, {
                    'veranstaltung': v.name,
                    'link_veranstalter': link_veranstalter + (link_suffix_format % (v.id, v.access_token)),
                })
                body = tools.render_email(data['body'], context)
                recipients = [person.email for person in v.veranstalter.all() if person.email]

                for person in v.veranstalter.all():
                    fg = person.fachgebiet
                    if fg is not None:
                        fg_mails = FachgebietEmail.objects.filter(fachgebiet=fg)
                        for fg_mail in fg_mails:
                            if (fg_mail.email_sekretaerin is not None) and (fg_mail.email_sekretaerin not in recipients):
                                recipients.append(fg_mail.email_sekretaerin)

                for p in v.veranstalter.all():
                    fg = p.fachgebiet
                    if fg is not None:
                        fg_mails = FachgebietEmail.objects.filter(fachgebiet=fg)
                        for fg_mail in fg_mails:
                            if (fg_mail.email_sekretaerin is not None) \
                                    and (fg_mail.email_sekretaerin not in recipients):
                                recipients.append(fg_mail.email_sekretaerin)

                if not recipients:
                    messages.warning(request,
                                     (u'An die Veranstalter von "%s" wurde keine Mail ' +
                                      u'verschickt, da keine Adressen hinterlegt waren.') % v.name)
                    continue
                mails.append((subject, body, settings.DEFAULT_FROM_EMAIL, recipients))

            # Kopie für das Feedback-Team
            subject = data['subject_rendered']
            body = tools.render_email(data['body'], demo_context)
            mails.append((subject, body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL]))

            # Mails senden
            send_mass_mail(mails)
            messages.success(request, '%d E-Mails wurden erfolgreich versandt!' % (len(mails)-1))
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
            warnings, errors, vcount, fbcount = parse_ergebnisse(semester, request.FILES['file'])
            if fbcount:
                messages.success(
                    request,
                    u'%u Veranstaltungen mit insgesamt %u Fragebögen wurden erfolgreich importiert.' % (vcount, fbcount)
                )
            else:
                warnings.append(u'Es konnten keine Fragebögen importiert werden.')

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
        messages.warning(request, u'Für das %s liegen keine Ergebnisse vor.' % semester)
    else:
        messages.success(request, u'Das Ranking für das %s wurde erfolgreich berechnet.' % semester)
    return HttpResponseRedirect(reverse('sync_ergebnisse'))


@user_passes_test(lambda u: u.is_superuser)
def ergebnisse(request):
    return public.index(request)
