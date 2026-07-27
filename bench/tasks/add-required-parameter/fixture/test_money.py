import pytest

from invoice import invoice_total
from money import format_amount
from receipt import receipt_line


def test_format_amount_requires_currency():
    assert format_amount(12.5, "USD") == "12.50 USD"
    with pytest.raises(TypeError):
        format_amount(12.5)


def test_invoice_total_passes_currency():
    assert invoice_total([1.0, 2.5], "EUR") == "Total: 3.50 EUR"


def test_receipt_line_passes_currency():
    assert receipt_line("Coffee", 3.0, "GBP") == "Coffee: 3.00 GBP"
