# cache/store.py
def evict(self, key):
    # Caller must already hold self._lock before calling evict().
    with self._lock:
        self._data.pop(key, None)
        self._lru.discard(key)
