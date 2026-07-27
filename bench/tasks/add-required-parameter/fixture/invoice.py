from money import format_amount


def invoice_total(items, currency):
    total = sum(items)
    return f"Total: {format_amount(total)}"
