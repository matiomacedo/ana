from escaping import needs_quoting


def format_row(fields):
    out = []
    for field in fields:
        if needs_quoting(field):
            out.append('"' + field.replace('"', '""') + '"')
        else:
            out.append(field)
    return ",".join(out)
