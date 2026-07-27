from repo import fetch_user


def greeting(uid):
    name, _email = fetch_user(uid)
    return f"Hello, {name}!"
