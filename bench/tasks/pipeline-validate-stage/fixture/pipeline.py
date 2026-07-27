from stages import enrich, normalize

STAGES = [normalize, enrich]


def run(record):
    for stage in STAGES:
        record = stage(record)
    return record
