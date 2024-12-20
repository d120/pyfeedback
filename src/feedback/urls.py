# coding=utf-8

from django.conf.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import feedback.views.public
import feedback.views.veranstalter
from feedback.views.public_class_view import VeranstaltungsDeadlines
import feedback.views.intern
import feedback.views.intern.vv
import feedback.views.intern.auth
from django.views.decorators.csrf import csrf_exempt
import django.contrib.auth.views
from django.urls import reverse_lazy, re_path
from django.conf import settings
from feedback.views.veranstalter import VeranstalterWizard
from django.utils.translation import get_language

if not settings.DEBUG:
    default_redirect = f'/{get_language()}/feedback/veranstalter/'
else:
    default_redirect = '/veranstalter/' # {'redirect_to': default_redirect}

# allgemeine Views
urlpatterns = [
    re_path(r'^$', feedback.views.redirect, {'redirect_to': default_redirect}, name="default"),
]

# öffentliche Views
urlpatterns += [
    re_path(r'^ergebnisse/(?P<vid>\d+)/$', feedback.views.public.veranstaltung, name='public-veranstaltung'),
    re_path(r'^ergebnisse/$', feedback.views.public.index, name='public-results'),
]

urlpatterns += [re_path(r'^deadlines/$', VeranstaltungsDeadlines.as_view(), name='Deadlines'),
                re_path(r'^barcodedrop/$', csrf_exempt(feedback.views.public.barcodedrop), name='barcodedrop'),]


# Veranstalter-Views
urlpatterns += [
    re_path(r'^veranstalter/login/$', feedback.views.veranstalter.login, name='veranstalter-login'),
    re_path(r'^veranstalter/logout/$',
        django.contrib.auth.views.LogoutView.as_view(),
        {'template_name': "veranstalter/logout.html"},
        name='veranstalter-logout'),

    re_path(r'^veranstalter/bestellung', VeranstalterWizard.as_view(), name='veranstalter-bestellung'),
    re_path(r'^veranstalter/', feedback.views.veranstalter.veranstalter_dashboard, name='veranstalter-index')
]

# interne Views
urlpatterns += [
    re_path(r'^intern/uebersicht/$', feedback.views.intern.index, name='intern-index'),
    re_path(r'^intern/sendmail/$', feedback.views.intern.sendmail, name='sendmail'),
    re_path(r'^intern/export_veranstaltungen/$', feedback.views.intern.export_veranstaltungen, name='export_veranstaltungen'),
    re_path(r'^intern/generate_letters/$', feedback.views.intern.generate_letters, name='generate_letters'),
    re_path(r'^intern/import_ergebnisse/$', feedback.views.intern.import_ergebnisse, name='import_ergebnisse'),
    re_path(r'^intern/status_final/$', feedback.views.intern.CloseOrderFormView.as_view(), name='status_final'),
    re_path(r'^intern/sync_ergebnisse/$', feedback.views.intern.sync_ergebnisse, name='sync_ergebnisse'),
    re_path(r'^intern/fragebogensprache/$', feedback.views.intern.fragebogensprache, name='fragebogensprache'),
    re_path(r'^intern/lange_ohne_evaluation/$', feedback.views.intern.lange_ohne_evaluation, name='lange_ohne_evaluation'),
    re_path(r'^intern/ergebnisse/$', feedback.views.intern.ergebnisse, name='intern-ergebnisse'),
    re_path(r'^intern/tans/$', feedback.views.intern.ProcessTANs.as_view(),
    name='process-tans'),
]

# interne Views: Vorlesungsverzeichnis
urlpatterns += [
    re_path(r'^intern/import_vv/$', feedback.views.intern.vv.import_vv, name='import_vv'),
    re_path(r'^intern/import_vv_edit/$', feedback.views.intern.vv.import_vv_edit, name='import_vv_edit'),
    re_path(r'^intern/import_vv_edit_users/$', feedback.views.intern.vv.PersonFormView.as_view(),
        name='import_vv_edit_users'),
    re_path(r'^intern/import_vv_edit_users/(?P<pk>\d+)/$', feedback.views.intern.vv.PersonFormUpdateView.as_view(),
        name='import_vv_edit_users_update'),
    re_path(r'^intern/import_vv_edit_users/(?P<pk>\d+)/namecheck/$', feedback.views.intern.vv.SimilarNamesView.as_view(),
        name='import_vv_edit_users_update_namecheck')
]

# interne Views: Authentifizierung
urlpatterns += [
    re_path(r'^intern/rechte_uebernehmen/$', feedback.views.intern.auth.rechte_uebernehmen, name='rechte-uebernehmen'),
    re_path(r'^intern/rechte_zuruecknehmen/$', feedback.views.intern.auth.rechte_zuruecknehmen, name='rechte_zuruecknehmen'),
    re_path(r'^intern/$', feedback.views.intern.auth.login, name='auth-login'),
]

# Logout
urlpatterns += [
    re_path(r'^logout/$', django.contrib.auth.views.LogoutView.as_view(), {'next_page': reverse_lazy('feedback:public-results')}, name='logout'),
]


if settings.DEBUG:
    # Ausschließlich in der Entwicklung nötig, damit statische Dateien (JS, CSS, Bilder...)
    # angezeigt werden. Im Server-Betrieb kümmert sich Apache darum.
    urlpatterns += [
        re_path(r'^d120de/(?P<tail>.*)$', feedback.views.redirect, {'redirect_to': 'http://www.d120.de/d120de/'}),
    ]

    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
