from django import template

register = template.Library()


@register.filter
def money(cents):
    return f"${(cents or 0) / 100:,.0f}"


@register.filter
def whole_money(cents):
    return f"${(cents or 0) / 100:,.0f}"
