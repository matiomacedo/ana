def parse_intervals(text):
    out = []
    for chunk in text.split(","):
        start, _, end = chunk.strip().partition("-")
        out.append((int(start), int(end)))
    return out
