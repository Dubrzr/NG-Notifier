import operator

from django import template


register = template.Library()


@register.filter(name='sort_hosts')
def list_sort(value):
    return sorted(value, key=operator.attrgetter('host'))


@register.filter(name='sort_groups')
def list_sort(value):
    return sorted(value, key=operator.attrgetter('name'))