# coding=utf-8

from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.models import User

from django.urls import re_path
from django.conf.urls.i18n import i18n_patterns

# Admin-Seiten konfigurieren
admin.autodiscover()
# admin.site.unregister((User, Group))

# Datenbank-Admin und Entwicklerdoku
urlpatterns = i18n_patterns(
    # Muss in dieser Reihenfolge stehen bleiben, da sonst /doc nicht funktioniert!
    re_path(r'^intern/admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^intern/admin/', admin.site.urls),
    re_path(r"^", include("feedback.urls")),
)

