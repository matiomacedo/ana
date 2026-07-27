from store import KeyValueStore


class Api:
    def __init__(self):
        self._store = KeyValueStore()

    def put(self, key, value):
        self._store.set(key, value)

    def fetch(self, key):
        return self._store.get(key)
