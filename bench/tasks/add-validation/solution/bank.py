def transfer(balances, src, dst, amount):
    if src not in balances:
        raise KeyError(src)
    if dst not in balances:
        raise KeyError(dst)
    if amount < 0:
        raise ValueError("amount must not be negative")
    if balances[src] < amount:
        raise ValueError("insufficient funds")
    balances[src] -= amount
    balances[dst] += amount
    return balances
