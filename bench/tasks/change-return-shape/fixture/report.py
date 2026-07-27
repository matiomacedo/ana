from repo import fetch_user


def contact_line(uid):
    name, email = fetch_user(uid)
    return f"{name} <{email}>"
