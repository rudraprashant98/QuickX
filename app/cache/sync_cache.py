"""Synchronous cache wrapper for genetic algorithm optimization."""
import hashlib
import json
from typing import Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()


class SyncCache:
    """Synchronous cache that uses Redis if available, otherwise in-memory fallback."""
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._memory_cache: dict[str, Any] = {}
        self._use_redis = False
        
        if REDIS_AVAILABLE:
            try:
                # Parse redis_url (e.g., "redis://localhost:6379/0")
                redis_url = settings.redis_url
                if redis_url.startswith("redis://"):
                    # Extract host, port, db
                    parts = redis_url.replace("redis://", "").split("/")
                    host_port = parts[0].split(":")
                    host = host_port[0] if host_port else "localhost"
                    port = int(host_port[1]) if len(host_port) > 1 else 6379
                    db = int(parts[1]) if len(parts) > 1 else 0
                    
                    self._redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
                    # Test connection
                    self._redis_client.ping()
                    self._use_redis = True
            except Exception:
                # Fallback to in-memory cache
                self._use_redis = False
    
    def _make_key(self, prefix: str, *args) -> str:
        """Create a cache key from arguments."""
        key_data = json.dumps(args, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, prefix: str, *args) -> Optional[Any]:
        """Get value from cache."""
        key = self._make_key(prefix, *args)
        
        if self._use_redis and self._redis_client:
            try:
                value = self._redis_client.get(key)
                if value is not None:
                    return json.loads(value)
            except Exception:
                pass
        
        # Fallback to memory cache
        return self._memory_cache.get(key)
    
    def set(self, prefix: str, *args, value: Any, ttl: int = 3600) -> None:
        """Set value in cache."""
        key = self._make_key(prefix, *args)
        value_json = json.dumps(value)
        
        if self._use_redis and self._redis_client:
            try:
                self._redis_client.setex(key, ttl, value_json)
                return
            except Exception:
                pass
        
        # Fallback to memory cache
        self._memory_cache[key] = value
    
    def clear(self, prefix: Optional[str] = None) -> None:
        """Clear cache entries (optionally by prefix)."""
        if self._use_redis and self._redis_client:
            try:
                if prefix:
                    pattern = f"{prefix}:*"
                    keys = self._redis_client.keys(pattern)
                    if keys:
                        self._redis_client.delete(*keys)
                else:
                    self._redis_client.flushdb()
            except Exception:
                pass
        
        # Clear memory cache
        if prefix:
            self._memory_cache = {k: v for k, v in self._memory_cache.items() if not k.startswith(f"{prefix}:")}
        else:
            self._memory_cache.clear()


# Global cache instance
sync_cache = SyncCache()

