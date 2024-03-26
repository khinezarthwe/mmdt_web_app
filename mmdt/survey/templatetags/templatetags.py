from django import template

register = template.Library()

@register.filter
def pluck(dictionary_list, key):
    return [d[key] for d in dictionary_list if key in d]