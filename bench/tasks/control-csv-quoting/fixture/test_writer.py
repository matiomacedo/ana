from writer import format_row


def test_plain_fields_unquoted():
    assert format_row(["a", "b"]) == "a,b"


def test_comma_field_quoted():
    assert format_row(["a,b", "c"]) == '"a,b",c'


def test_inner_quotes_doubled():
    assert format_row(['say "hi"']) == '"say ""hi"""'


def test_newline_field_quoted():
    assert format_row(["one\ntwo"]) == '"one\ntwo"'
