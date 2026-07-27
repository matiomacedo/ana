from repo import all_users


def name_of(uid):
    user = all_users().get(uid)
    return user["name"] if user else None
