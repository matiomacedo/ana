def domain_of(user):
    return user.email_address.split("@")[1]
