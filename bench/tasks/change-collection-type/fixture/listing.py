from repo import all_users


def names():
    return sorted(u["name"] for u in all_users())
