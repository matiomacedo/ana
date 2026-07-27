from repo import fetch_user


def greeting(uid):
    user = fetch_user(uid)
    return f"Hello, {user['name']}!"
