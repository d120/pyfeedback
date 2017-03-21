# coding=utf-8

from base64 import b64decode

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import RemoteUserBackend, ModelBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.utils.encoding import smart_text

from feedback.models.base import Veranstaltung


# ------------------------------ Login mit Veranstalter-Rechten ------------------------------ #

class VeranstalterBackend(ModelBackend):
    def authenticate(self, vid, token):
        if not (vid and token):
            return None

        if not Veranstaltung.objects.filter(id=vid, access_token=token).exists():
            return None

        try:
            return User.objects.get(username=settings.USERNAME_VERANSTALTER)
        except User.DoesNotExist:
            return None


class TakeoverBackend(ModelBackend):
    def authenticate(self, user, current_user=None, reset=False):
        if reset or (current_user and current_user.is_superuser):
            return user
        return None


# ------------------------------ Nutzung eines Fachschaftsaccounts ------------------------------ #

class FSAccountBackend(RemoteUserBackend):
    # Login wird automatisch über RemoteUserMiddleware bzw. RemoteUserBackend abgewickelt,
    # hier muss nur noch der neue User konfiguriert werden.
    def configure_user(self, user):
        user.email = user.username + '@d120.de'
        user.is_staff = True
        user.is_superuser = True
        user.set_unusable_password()
        user.save()
        return user

    # Wenn wenn wir in Debug sind muss der Nutzername erst aus HTTP_AUTHORIZATION encoding
    # umgewandelt werden.
    def clean_username(self, username):
        if settings.DEBUG:
            credentials = b64decode(username.split()[1])
            user = credentials.split(':')[0]
            return (smart_text(user))

        else:
            return username


class FSDebugRemoteUserMiddleware(RemoteUserMiddleware):
    if settings.DEBUG:
        header = 'HTTP_AUTHORIZATION'
