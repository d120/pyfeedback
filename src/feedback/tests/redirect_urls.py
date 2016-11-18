# coding=utf-8

from django.conf.urls import url
from feedback.views import redirect

urlpatterns = [
    url(r'^redirect/$', redirect,
        {'redirect_to': 'http://www.d120.de/'}),
    url(r'^redirect/(?P<tail>.*)$', redirect,
        {'redirect_to': 'http://www.d120.de/'}),
]
