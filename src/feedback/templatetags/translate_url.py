from django import template
from django.urls import resolve, reverse, Resolver404
from django.utils import translation

register = template.Library()

@register.simple_tag(takes_context=True)
def translate_url(context, language):
    """
    Used to translate URLs for switching languages.
    """
    if "request" not in context:
        return ""

    try:
        view = resolve(context["request"].path_info)
    except Resolver404:
        return ""

    request_language = translation.get_language()

    try:
        translation.activate(language)

        namespace = view.namespace
        view_name = f"{namespace}:{view.url_name}" if namespace else view.url_name

        return reverse(
            view_name,
            args=view.args,
            kwargs=view.kwargs,
        )
    finally:
        translation.activate(request_language)
