# coding=utf-8

from django.urls import re_path
from feedback.views import redirect

urlpatterns = [
    re_path(r'^redirect/$', redirect,
        {'redirect_to': 'http://www.d120.de/'}),
    re_path(r'^redirect/(?P<tail>.*)$', redirect,
        {'redirect_to': 'http://www.d120.de/'}),
]
