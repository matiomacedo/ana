USERS = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


def all_users():
    return {user["id"]: user for user in USERS}
