from policy import BASE_DELAY, MAX_DELAY


def backoff_delays(attempts):
    delays = []
    delay = BASE_DELAY
    for _ in range(attempts):
        delays.append(min(delay, MAX_DELAY))
        delay *= 2
    return delays
