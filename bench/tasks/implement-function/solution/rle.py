def rle_encode(text):
    """Run-length encode a string: 'aaabb' -> 'a3b2'. Empty string -> ''."""
    if not text:
        return ""
    out = []
    current = text[0]
    count = 1
    for ch in text[1:]:
        if ch == current:
            count += 1
        else:
            out.append(f"{current}{count}")
            current, count = ch, 1
    out.append(f"{current}{count}")
    return "".join(out)
