# coding=utf-8

from django.urls import re_path
from feedback.views import redirect
from django.conf.urls.i18n import i18n_patterns


urlpatterns = i18n_patterns(
    re_path(r'^redirect/$', redirect,
        {'redirect_to': 'http://www.d120.de/'}),
    re_path(r'^redirect/(?P<tail>.*)$', redirect,
        {'redirect_to': 'http://www.d120.de/'}),
)
