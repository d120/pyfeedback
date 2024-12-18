from django import template
from django.urls import resolve, reverse
from django.utils import translation

register = template.Library()

@register.simple_tag(takes_context=True)
def translate_url(context, language):
    '''
    used to translate urls for switching languages
    '''
    ## this if is here only because of veranstalter.py > VeranstalterWizard > done method.
    ## see comment there, why we might not have request
    if 'request' in context :
        view = resolve(context['request'].path)
        request_language = translation.get_language()
        translation.activate(language)
        url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
        translation.activate(request_language)
        return url
    return ""