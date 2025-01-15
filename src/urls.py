# coding=utf-8

from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.models import User

from django.urls import re_path, reverse_lazy, path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

# Admin-Seiten konfigurieren
admin.autodiscover()
# admin.site.unregister((User, Group))

urlpatterns = [
    path('accounts/', include('allauth.urls')),
]

urlpatterns += [
    re_path(r'^$', RedirectView.as_view(url=reverse_lazy("feedback:default"), permanent=True), name='no-path'),
]

# Datenbank-Admin und Entwicklerdoku
urlpatterns += i18n_patterns(
    # Muss in dieser Reihenfolge stehen bleiben, da sonst /doc nicht funktioniert!
    re_path(r'^intern/admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^intern/admin/', admin.site.urls),
    re_path(r'^', include(("feedback.urls", "feedback"), namespace="feedback")),
)

urlpatterns += staticfiles_urlpatterns()

if not settings.DEBUG :
    # don't forget to put sample favicon.ico in static files
    urlpatterns += [path('favicon.ico', RedirectView.as_view(url='/feedback/static/img/favicon.ico', permanent=True))]
