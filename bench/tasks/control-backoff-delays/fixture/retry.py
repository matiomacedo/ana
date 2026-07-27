from policy import BASE_DELAY, MAX_DELAY


def backoff_delays(attempts):
    return [BASE_DELAY * attempt for attempt in range(attempts)]
