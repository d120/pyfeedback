# coding=utf-8

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import feedback.views.public
import feedback.views.veranstalter
from feedback.views.public_class_view import VeranstaltungsDeadlines
import feedback.views.intern
import feedback.views.intern.vv
import feedback.views.intern.auth
from django.views.decorators.csrf import csrf_exempt
import django.contrib.auth.views
from django.urls import reverse_lazy
from django.conf import settings
from feedback.views.veranstalter import VeranstalterWizard


# Admin-Seiten konfigurieren
admin.autodiscover()
# admin.site.unregister((User, Group))

if not settings.DEBUG:
    default_redirect = '/feedback-new/'
else:
    default_redirect = '/veranstalter/'

# Datenbank-Admin und Entwicklerdoku
urlpatterns = [
    # Muss in dieser Reihenfolge stehen bleiben, da sonst /doc nicht funktioniert!
    url(r'^intern/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^intern/admin/', include(admin.site.urls)),
]

# allgemeine Views
urlpatterns += [
    url(r'^$', feedback.views.redirect, {'redirect_to': default_redirect}),
]

# öffentliche Views
urlpatterns += [
    url(r'^ergebnisse/(?P<vid>\d+)/$', feedback.views.public.veranstaltung, name='public-veranstaltung'),
    url(r'^ergebnisse/$', feedback.views.public.index, name='public-results'),
]

urlpatterns += [url(r'^deadlines/$', VeranstaltungsDeadlines.as_view(), name='Deadlines'),
                url(r'^barcodedrop/$', csrf_exempt(feedback.views.public.barcodedrop), name='barcodedrop'),]


# Veranstalter-Views
urlpatterns += [
    url(r'^veranstalter/login/$', feedback.views.veranstalter.login, name='veranstalter-login'),
    url(r'^veranstalter/bestellung', VeranstalterWizard.as_view(), name='veranstalter-bestellung'),
    url(r'^veranstalter/', feedback.views.veranstalter.veranstalter_dashboard, name='veranstalter-index')
]

# interne Views
urlpatterns += [
    url(r'^intern/uebersicht/$', feedback.views.intern.index, name='intern-index'),
    url(r'^intern/sendmail/$', feedback.views.intern.sendmail, name='sendmail'),
    url(r'^intern/export_veranstaltungen/$', feedback.views.intern.export_veranstaltungen, name='export_veranstaltungen'),
    url(r'^intern/generate_letters/$', feedback.views.intern.generate_letters, name='generate_letters'),
    url(r'^intern/import_ergebnisse/$', feedback.views.intern.import_ergebnisse, name='import_ergebnisse'),
    url(r'^intern/status_final/$', feedback.views.intern.CloseOrderFormView.as_view(), name='status_final'),
    url(r'^intern/sync_ergebnisse/$', feedback.views.intern.sync_ergebnisse, name='sync_ergebnisse'),
    url(r'^intern/fragebogensprache/$', feedback.views.intern.fragebogensprache, name='fragebogensprache'),
    url(r'^intern/lange_ohne_evaluation/$', feedback.views.intern.lange_ohne_evaluation, name='lange_ohne_evaluation'),
    url(r'^intern/ergebnisse/$', feedback.views.intern.ergebnisse, name='intern-ergebnisse'),

]

# interne Views: Vorlesungsverzeichnis
urlpatterns += [
    url(r'^intern/import_vv/$', feedback.views.intern.vv.import_vv, name='import_vv'),
    url(r'^intern/import_vv_edit/$', feedback.views.intern.vv.import_vv_edit, name='import_vv_edit'),
    url(r'^intern/import_vv_edit_users/$', feedback.views.intern.vv.PersonFormView.as_view(),
        name='import_vv_edit_users'),
    url(r'^intern/import_vv_edit_users/(?P<pk>\d+)/$', feedback.views.intern.vv.PersonFormUpdateView.as_view(),
        name='import_vv_edit_users_update'),
    url(r'^intern/import_vv_edit_users/(?P<pk>\d+)/namecheck/$', feedback.views.intern.vv.SimilarNamesView.as_view(),
        name='import_vv_edit_users_update_namecheck')
]

# interne Views: Authentifizierung
urlpatterns += [
    url(r'^intern/rechte_uebernehmen/$', feedback.views.intern.auth.rechte_uebernehmen, name='rechte-uebernehmen'),
    url(r'^intern/rechte_zuruecknehmen/$', feedback.views.intern.auth.rechte_zuruecknehmen, name='rechte_zuruecknehmen'),
    url(r'^intern/$', feedback.views.intern.auth.login, name='auth-login'),
]

# Logout
urlpatterns += [
    url(r'^logout/$', django.contrib.auth.views.logout, {'next_page': reverse_lazy('public-results')}, name='logout'),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    # Ausschließlich in der Entwicklung nötig, damit statische Dateien (JS, CSS, Bilder...)
    # angezeigt werden. Im Server-Betrieb kümmert sich Apache darum.
    urlpatterns += [
    url(r'^d120de/(?P<tail>.*)$', feedback.views.redirect,
        {'redirect_to': 'http://www.d120.de/d120de/'}),
    ]

    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
