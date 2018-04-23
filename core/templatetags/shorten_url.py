import urlparse

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name='shorten_url')
@stringfilter
def shorten_url(url):
    result = urlparse.urlparse(url)
    return str(result.hostname)
