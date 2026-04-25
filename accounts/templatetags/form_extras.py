from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def get_field(form, name):
    return form.fields.get(name) and form[name]


@register.filter
def rupiah(value):
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")

    amount = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"Rp {formatted}"
