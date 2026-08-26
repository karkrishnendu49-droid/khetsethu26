import time

class TTLCache:
    def __init__(self): self.store = {}
    def get(self, key):
        item = self.store.get(key)
        if not item: return None
        if time.time() > item[0]:
            self.store.pop(key, None)
            return None
        return item[1]
    def set(self, key, value, ttl):
        self.store[key] = (time.time() + ttl, value)

geocode_cache = TTLCache()   # 24h entries
route_cache = TTLCache()     # 6h entries
weather_cache = TTLCache()   # 30min entries
market_cache = TTLCache()    # 1h entries
