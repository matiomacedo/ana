def transfer(balances, src, dst, amount):
    balances[src] -= amount
    balances[dst] += amount
    return balances
