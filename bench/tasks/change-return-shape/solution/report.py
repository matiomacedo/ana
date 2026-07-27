from repo import fetch_user


def contact_line(uid):
    user = fetch_user(uid)
    return f"{user['name']} <{user['email']}>"
