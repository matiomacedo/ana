from money import format_amount


def receipt_line(label, value, currency):
    return f"{label}: {format_amount(value, currency)}"
