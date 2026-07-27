USERS = {
    1: ("Alice", "alice@example.com"),
    2: ("Bob", "bob@example.org"),
}


def fetch_user(uid):
    name, email = USERS[uid]
    return {"name": name, "email": email}
