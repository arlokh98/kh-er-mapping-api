# priority_cache_manager.py

import hashlib
from collections import OrderedDict

class PriorityCacheManager:
    def __init__(self, original_capacity=7, scaled_capacity=7):
        self.original_capacity = original_capacity
        self.scaled_capacity = scaled_capacity
        self.original_cache = OrderedDict()
        self.scaled_cache = OrderedDict()
        self.batch_tracker = set()
        self.er_cache_reset_recently = False

    def _make_key(self, url):
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def get_original(self, url):
        key = self._make_key(url)
        return self.original_cache.get(key)

    def store_original(self, url, image):
        key = self._make_key(url)
        batch_id = self._extract_batch_tag(url)
        
        if batch_id in {"1", "2"} and batch_id not in self.batch_tracker:
            self._reset_all()
        
        if batch_id:
            self.batch_tracker.add(batch_id)

        if key not in self.original_cache:
            if len(self.original_cache) >= self.original_capacity:
                self.original_cache.popitem(last=False)
            self.original_cache[key] = image

    def get_scaled(self, url):
        key = self._make_key(url)
        return self.scaled_cache.get(key)

    def store_scaled(self, url, image):
        key = self._make_key(url)
        if key not in self.scaled_cache:
            if len(self.scaled_cache) >= self.scaled_capacity:
                self.scaled_cache.popitem(last=False)
            self.scaled_cache[key] = image

    def get_cache_status(self):
        return {
            "original_cache_keys": list(self.original_cache.keys()),
            "scaled_cache_keys": list(self.scaled_cache.keys()),
            "batch_tracker": list(self.batch_tracker),
            "er_cache_reset_recently": self.er_cache_reset_recently
        }

    def _extract_batch_tag(self, url):
        if "?" not in url:
            return None
        parts = url.split("?")[1].split("&")
        for part in parts:
            if part.startswith("batch="):
                return part.split("=")[1]
        return None

    def _reset_all(self):
        self.original_cache.clear()
        self.scaled_cache.clear()
        self.batch_tracker.clear()
        self.er_cache_reset_recently = True

# ✅ Lazy loader to avoid circular imports
_cache_instance = None

def get_priority_cache():
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PriorityCacheManager(original_capacity=7, scaled_capacity=7)
    return _cache_instance
