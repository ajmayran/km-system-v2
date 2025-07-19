from django import template

register = template.Library()

@register.filter
def first_100_words(value):
    words = value.split()
    return " ".join(words[:100])
