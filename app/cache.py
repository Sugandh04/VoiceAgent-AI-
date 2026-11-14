"""
app/cache.py
━━━━━━━━━━━
Async Redis cache layer for VoiceAgent AI.

Provides:
  - get / set / delete with optional TTL
  - JSON serialization / deserialization helpers
  - Graceful degradation — all methods are safe no-ops if Redis package
    is not installed or if Redis server is unavailable (local dev mode).

Usage:
    from app.cache import cache

    data = await cache.get_json("dashboard:stats:42")
    if data is None:
        data = await compute_expensive_stats(user_id=42)
        await cache.set_json("dashboard:stats:42", data, ttl=30)
"""

import json
import logging
from typing import Any, Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from app.config import settings

logger = logging.getLogger("cache")


class RedisCache:
    """
    Async Redis cache wrapper with transparent JSON serialization.

    All public methods silently swallow connection errors and return
    None / False — the caller falls back to the database automatically.
    This prevents Redis unavailability from taking down the API.
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None

    async def connect(self) -> None:
        """
        Initialise the Redis connection pool.
        Called once from the FastAPI lifespan startup handler.
        """
        if aioredis is None:
            logger.info("ℹ️  'redis' package not installed. Cache disabled — falling back to DB.")
            self._client = None
            return

        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        try:
            self._client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await self._client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except Exception as exc:
            logger.warning(
                f"⚠️  Redis unavailable ({exc}). Cache disabled — falling back to DB."
            )
            self._client = None

    async def disconnect(self) -> None:
        """Close the connection pool on application shutdown."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            logger.info("Redis connection closed.")

    # ── Core primitives ──────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        """Return raw string value or None on miss / error."""
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as exc:
            logger.debug(f"[Cache.get] key={key} error={exc}")
            return None

    async def set(self, key: str, value: str, ttl: int = 60) -> bool:
        """Store a raw string value with TTL (seconds). Returns False on error."""
        if not self._client:
            return False
        try:
            await self._client.setex(key, ttl, value)
            return True
        except Exception as exc:
            logger.debug(f"[Cache.set] key={key} error={exc}")
            return False

    async def delete(self, key: str) -> bool:
        """Invalidate a cache key. Returns False on error."""
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as exc:
            logger.debug(f"[Cache.delete] key={key} error={exc}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a glob pattern (e.g. ``dashboard:stats:*``).
        Uses SCAN to find keys and UNLINK for atomic non-blocking batch removal.
        """
        if not self._client:
            return 0
        deleted = 0
        try:
            keys = [key async for key in self._client.scan_iter(pattern)]
            if keys:
                deleted = await self._client.unlink(*keys)
        except Exception as exc:
            logger.debug(f"[Cache.delete_pattern] pattern={pattern} error={exc}")
        return deleted

    # ── JSON helpers ─────────────────────────────────────────────────────────

    async def get_json(self, key: str) -> Optional[Any]:
        """Deserialize a cached JSON value. Returns None on miss or parse error."""
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            await self.delete(key)  # remove corrupt entry
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Serialize value to JSON and cache it with TTL."""
        try:
            return await self.set(key, json.dumps(value, default=str), ttl=ttl)
        except (TypeError, ValueError) as exc:
            logger.warning(f"[Cache.set_json] Serialization error key={key}: {exc}")
            return False

    # ── Pub/Sub for WebSocket event bus ──────────────────────────────────────

    async def publish(self, channel: str, message: Any) -> bool:
        """Publish a JSON message to a Redis pub/sub channel."""
        if not self._client:
            return False
        try:
            await self._client.publish(channel, json.dumps(message, default=str))
            return True
        except Exception as exc:
            logger.debug(f"[Cache.publish] channel={channel} error={exc}")
            return False

    def pubsub(self) -> Optional[Any]:
        """Return a PubSub handle or None if Redis is unavailable."""
        return self._client.pubsub() if self._client else None

    @property
    def is_available(self) -> bool:
        return self._client is not None


# Singleton instance — imported throughout the app
cache = RedisCache()
