import threading
from urllib.parse import urlparse, parse_qs

class PriorityCacheManager:
    def __init__(self, original_capacity=6, scaled_capacity=12):
        self.original_capacity = original_capacity
        self.scaled_capacity = scaled_capacity

        self.er_batch_order = []  # Most recent 3 ER batches tracked
        self.nr_batch_order = []  # Most recent 3 NR batches tracked

        self.current_er_batches = {}  # batch_number: url
        self.current_nr_batches = {}  # batch_number: url

        self.original_cache = {}  # url: PIL.Image
        self.scaled_cache = {}   # (url, scale): PIL.Image

        self.lock = threading.Lock()

    def _update_batch_tracking(self, map_type, batch_number, url):
        with self.lock:
            batch_dict = self.current_er_batches if map_type == 'ER' else self.current_nr_batches
            batch_order = self.er_batch_order if map_type == 'ER' else self.nr_batch_order

            if batch_number not in batch_order:
                batch_order.append(batch_number)

            batch_dict[batch_number] = url

            # If more than 3 active batches tracked, evict oldest
            if len(batch_order) > 3:
                oldest_batch = batch_order.pop(0)
                old_url = batch_dict.pop(oldest_batch, None)
                if old_url:
                    self.evict_url(old_url)

    def evict_url(self, url):
        if url in self.original_cache:
            del self.original_cache[url]
        keys_to_remove = [(u, s) for (u, s) in self.scaled_cache.keys() if u == url]
        for key in keys_to_remove:
            del self.scaled_cache[key]

    def store_original(self, url, image):
        batch_number, map_type = self.parse_batch_and_type(url)
        if batch_number and map_type:
            self._update_batch_tracking(map_type, batch_number, url)

        with self.lock:
            if url not in self.original_cache:
                if len(self.original_cache) >= self.original_capacity:
                    oldest_url = next(iter(self.original_cache))
                    del self.original_cache[oldest_url]
                self.original_cache[url] = image

    def get_original(self, url):
        with self.lock:
            return self.original_cache.get(url, None)

    def store_scaled(self, url, scale, image):
        with self.lock:
            if (url, scale) not in self.scaled_cache:
                if len(self.scaled_cache) >= self.scaled_capacity:
                    oldest_key = next(iter(self.scaled_cache))
                    del self.scaled_cache[oldest_key]
                self.scaled_cache[(url, scale)] = image

    def get_scaled(self, url, scale):
        with self.lock:
            return self.scaled_cache.get((url, scale), None)

    def get_cache_status(self):
        with self.lock:
            return {
                "original_cache_count": len(self.original_cache),
                "scaled_cache_count": len(self.scaled_cache),
                "active_er_batches": self.current_er_batches,
                "active_nr_batches": self.current_nr_batches
            }

    @staticmethod
    def parse_batch_and_type(url):
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        batch = query_params.get('batch', [None])[0]
        map_type = query_params.get('type', [None])[0]
        return batch, map_type
