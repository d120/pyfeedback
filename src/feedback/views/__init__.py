# coding=utf-8

from django.http import HttpResponsePermanentRedirect
from django.views.decorators.http import require_safe


@require_safe
def redirect(request, redirect_to, tail=''):
    return HttpResponsePermanentRedirect(redirect_to + tail)
