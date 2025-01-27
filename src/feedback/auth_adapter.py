from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.conf import settings

class FeedbackSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        user = sociallogin.user

        if not user.id:
            try :
                existing_user = User.objects.get(username=user.username)
                sociallogin.connect(request, existing_user)
                user = existing_user
            except User.DoesNotExist :
                user.save()

        user.is_superuser = True
        user.is_staff = True
        user.save()