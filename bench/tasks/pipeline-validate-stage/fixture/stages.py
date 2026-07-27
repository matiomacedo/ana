def normalize(record):
    return {**record, "name": record["name"].strip().lower()}


def enrich(record):
    return {**record, "domain": record["email"].split("@")[1]}
