from store import KeyValueStore


class Api:
    def __init__(self):
        self._store = KeyValueStore()

    def put(self, key, value):
        self._store.set(key, value)

    def fetch(self, key):
        return self._store.get(key)

    def remove(self, key):
        self._store._data.pop(key, None)

    def keys(self):
        return list(self._store._data)
