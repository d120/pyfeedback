# coding=utf-8

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_safe, require_http_methods

from feedback.models import Veranstaltung


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(('HEAD', 'GET', 'POST'))
def rechte_uebernehmen(request):
    data = {}

    if request.method == 'POST':
        try:
            orig_uid = request.user.id
            v = request.POST['vid']
            u = User.objects.get(username=settings.USERNAME_VERANSTALTER)
            veranst = Veranstaltung.objects.get(id=v)

            user = auth.authenticate(user=u, current_user=request.user)
            auth.login(request, user)
            request.session['orig_uid'] = orig_uid
            request.session['vid'] = v
            request.session['veranstaltung'] = unicode(veranst)

            if veranst.status is Veranstaltung.STATUS_BESTELLUNG_LIEGT_VOR or Veranstaltung.STATUS_BESTELLUNG_GEOEFFNET:
                return HttpResponseRedirect(reverse('veranstalter-index'))
            else:
                messages.warning(request, u'Fehler beim übernehmen der Rechte. '
                                          u'Der Status der Veranstaltung ist nicht berechtigt.')
        except KeyError:
            pass

    data['veranstaltungen'] = Veranstaltung.objects.order_by('semester', 'name').prefetch_related('semester')
    return render(request, 'intern/rechte_uebernehmen.html', data)


@login_required
@require_safe
def rechte_zuruecknehmen(request):
    # return is tried but no previous uid exists
    try:
        uid = request.session['orig_uid']  # this line throws the exception
        u = User.objects.get(id=uid)
        user = auth.authenticate(reset=True, user=u)
        auth.login(request, user)
        return HttpResponseRedirect(reverse('intern-index'))
    # Redirect to intern.index view to get a clear session
    except KeyError:
        return HttpResponseRedirect(reverse('intern-index'))


@require_safe
def login(request):
    if settings.DEBUG and not request.user.is_superuser:
        # "HTTP 401 Authorization Required" senden, damit man den Admin-Login testen kann
        if not 'HTTP_AUTHORIZATION' in request.META:
            response = HttpResponse(status=401)
            response['WWW-Authenticate'] = 'Basic realm="Feedback"'
            return response

    # Apache fordert User zum Login mit FS-Account auf, von daher muss hier nur noch weitergeleitet
    # werden.
    return HttpResponseRedirect(reverse('intern-index'))
