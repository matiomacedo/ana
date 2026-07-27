from repo import all_users


def name_of(uid):
    for user in all_users():
        if user["id"] == uid:
            return user["name"]
    return None
