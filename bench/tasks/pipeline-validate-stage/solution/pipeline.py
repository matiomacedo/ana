from stages import enrich, normalize, validate

STAGES = [validate, normalize, enrich]


def run(record):
    for stage in STAGES:
        record = stage(record)
    return record
