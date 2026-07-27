def validate(record):
    if "@" not in record["email"]:
        raise ValueError(f"invalid email: {record['email']}")
    return record


def normalize(record):
    return {**record, "name": record["name"].strip().lower()}


def enrich(record):
    return {**record, "domain": record["email"].split("@")[1]}
