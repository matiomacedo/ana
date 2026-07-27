from stages import enrich, normalize


def validate(record):
    if "@" not in record["email"]:
        raise ValueError("bad email")
    return record


STAGES = [validate, normalize, enrich]


def run(record):
    for stage in STAGES:
        record = stage(record)
    return record
