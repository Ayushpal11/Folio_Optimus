import redis.asyncio as aioredis
import json
import os
from typing import Any, Optional
from datetime import timedelta

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        await redis_client.ping()
        print("✓ Redis connected")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}")
        redis_client = None


async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def get_cached(key: str) -> Optional[Any]:
    """Get value from cache"""
    if not redis_client:
        return None
    try:
        val = await redis_client.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


async def set_cached(key: str, data: Any, ttl: int = 300):
    """Set value in cache with TTL (seconds)"""
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(data), ex=ttl)
    except Exception as e:
        print(f"Cache set error: {e}")


async def delete_cached(key: str):
    """Delete value from cache"""
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception as e:
        print(f"Cache delete error: {e}")


async def clear_cache_pattern(pattern: str):
    """Clear all cache keys matching pattern"""
    if not redis_client:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache clear error: {e}")


async def increment_counter(key: str, value: int = 1, ttl: int = 60) -> int:
    """Increment counter for rate limiting"""
    if not redis_client:
        return 0
    try:
        result = await redis_client.incr(key, value)
        if result == value:  # First increment, set TTL
            await redis_client.expire(key, ttl)
        return result
    except Exception as e:
        print(f"Counter increment error: {e}")
        return 0


async def get_counter(key: str) -> int:
    """Get counter value"""
    if not redis_client:
        return 0
    try:
        val = await redis_client.get(key)
        return int(val) if val else 0
    except Exception as e:
        print(f"Counter get error: {e}")
        return 0
