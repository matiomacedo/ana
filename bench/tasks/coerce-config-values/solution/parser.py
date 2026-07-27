def parse_line(line):
    name, _, value = line.partition("=")
    value = value.split("#")[0]
    return name.strip(), value.strip()


def parse(text):
    result = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name, value = parse_line(line)
        result[name] = value
    return result
