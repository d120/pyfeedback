# coding=utf-8

from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from feedback.models import Semester, get_model, Veranstaltung, Kommentar

from django.conf import settings


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
    data['parts'] = zip(parts, ergebnis.values())
    data['ergebnis'] = ergebnis

    try:
        data['kommentar'] = Kommentar.objects.get(veranstaltung=veranstaltung)
    except Kommentar.DoesNotExist:
        pass

    return render(request, 'public/veranstaltung.html', data)
