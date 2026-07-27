SPECIAL = (",", '"', "\n")


def needs_quoting(field):
    return any(ch in field for ch in SPECIAL)
