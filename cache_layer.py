"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V260-CTO-CACHE-LAYER-AHMAD-20260727                        ║
║  cache_layer.py v2.6.0 - Thread-safe TTL cache                  ║
║  Date: 2026-07-27 | Leader: Dr. Ahmad Al-Fanni (CTO)            ║
╚══════════════════════════════════════════════════════════════════╝

Features:
  - Thread-safe (uses RLock)
  - TTL-based expiration (default 30 min)
  - Automatic cleanup of expired entries
  - Statistics tracking (hits/misses)
  - Memory-safe (max entries limit)
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict


class TTLCache:
    """Thread-safe TTL cache with LRU eviction."""

    def __init__(self, ttl_seconds: int = 1800, max_size: int = 500):
        """
        Args:
            ttl_seconds: Time-to-live in seconds (default 30 min)
            max_size: Maximum number of entries (default 500)
        """
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._data: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get a value if it exists and is not expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            value, expiry = entry
            if time.time() > expiry:
                # Expired
                del self._data[key]
                self._stats["misses"] += 1
                return None

            # Move to end (LRU refresh)
            self._data.move_to_end(key)
            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with optional custom TTL."""
        with self._lock:
            ttl = ttl if ttl is not None else self.ttl
            expiry = time.time() + ttl

            # Evict oldest if at capacity
            if key not in self._data and len(self._data) >= self.max_size:
                oldest = next(iter(self._data))
                del self._data[oldest]
                self._stats["evictions"] += 1

            self._data[key] = (value, expiry)
            self._data.move_to_end(key)
            self._stats["sets"] += 1

    def delete(self, key: str) -> bool:
        """Remove a key. Returns True if it existed."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._data.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        with self._lock:
            now = time.time()
            expired_keys = [k for k, (_, exp) in self._data.items() if now > exp]
            for k in expired_keys:
                del self._data[k]
            return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            total_reqs = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_reqs * 100) if total_reqs > 0 else 0
            return {
                **self._stats,
                "size": len(self._data),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "hit_rate_pct": round(hit_rate, 2),
                "total_requests": total_reqs,
            }


# ═══════════════════════════════════════════════════════════════
# Global singleton for lookup cache
# ═══════════════════════════════════════════════════════════════
_LOOKUP_CACHE = TTLCache(ttl_seconds=1800, max_size=500)  # 30 min


def get_cached_lookup(username: str) -> Optional[Any]:
    """Get cached TikTok lookup result for a username."""
    key = f"lookup:{username.lower().strip().lstrip('@')}"
    return _LOOKUP_CACHE.get(key)


def cache_lookup(username: str, result: Any, ttl: Optional[int] = None) -> None:
    """Cache a TikTok lookup result. Only cache successful results."""
    if not result:
        return
    # Don't cache errors
    if hasattr(result, 'success') and not result.success:
        return
    if isinstance(result, dict) and not result.get('success', True):
        return
    key = f"lookup:{username.lower().strip().lstrip('@')}"
    _LOOKUP_CACHE.set(key, result, ttl=ttl)


def clear_cache() -> None:
    """Clear all cached entries."""
    _LOOKUP_CACHE.clear()


def cache_stats() -> Dict[str, Any]:
    """Return cache statistics."""
    return _LOOKUP_CACHE.stats()


def cleanup_cache() -> int:
    """Remove expired entries manually."""
    return _LOOKUP_CACHE.cleanup_expired()


if __name__ == "__main__":
    # Self-test
    c = TTLCache(ttl_seconds=2, max_size=3)
    c.set("a", 1); c.set("b", 2); c.set("c", 3)
    assert c.get("a") == 1
    c.set("d", 4)  # evicts b (a was refreshed)
    assert c.get("b") is None
    print("✅ cache_layer.py self-test passed")
    print(f"Stats: {c.stats()}")
