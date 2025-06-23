"""
Response caching for Gemini API
"""

import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from .common import logger


class ResponseCache:
    """Thread-safe response cache with TTL"""

    def __init__(self, ttl: timedelta = timedelta(minutes=15)):
        self.cache: Dict[str, Tuple[datetime, str]] = {}
        self.ttl = ttl
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _generate_key(
        self, prompt: str, model: str, generation_config: Dict[str, Any]
    ) -> str:
        """Generate a cache key from request parameters"""
        cache_data = {
            "prompt": prompt,
            "model": model,
            "config": generation_config,
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(
        self, prompt: str, model: str, generation_config: Dict[str, Any]
    ) -> Optional[str]:
        """Get a cached response if available and not expired"""
        key = self._generate_key(prompt, model, generation_config)

        with self.lock:
            if key in self.cache:
                timestamp, response = self.cache[key]
                if datetime.now() - timestamp < self.ttl:
                    self.hits += 1
                    logger.debug("Cache hit for key %s", key[:8])
                    return response
                else:
                    # Expired entry
                    del self.cache[key]

            self.misses += 1
            return None

    def put(
        self, prompt: str, model: str, generation_config: Dict[str, Any], response: str
    ) -> None:
        """Store a response in the cache"""
        key = self._generate_key(prompt, model, generation_config)

        with self.lock:
            self.cache[key] = (datetime.now(), response)
            logger.debug("Cached response for key %s", key[:8])

            # Clean old entries periodically
            if len(self.cache) % 100 == 0:
                self._clean_expired()

    def _clean_expired(self) -> None:
        """Remove expired entries from the cache"""
        now = datetime.now()
        expired_keys = [
            key
            for key, (timestamp, _) in self.cache.items()
            if now - timestamp > self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug("Removed %s expired cache entries", len(expired_keys))

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0

            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "size": len(self.cache),
                "ttl_minutes": self.ttl.total_seconds() / 60,
            }

    def clear(self) -> None:
        """Clear the entire cache"""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")

    # Backward compatibility method
    def set(self, prompt: str, config: Dict[str, Any], response: str) -> None:
        """Backward compatible set method (uses default model)"""
        self.put(prompt, "default", config, response)
