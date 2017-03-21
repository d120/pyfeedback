from django import template

register = template.Library()


@register.filter(name='range')
def filter_range(start, end):
    # workaround in templates: "for i in start_index|range:end_index"
    return list(range(start, end))
