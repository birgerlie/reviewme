"""
Redis Cache Service Implementation
Implements ICacheService interface using Redis
"""
import json
from typing import Optional, Any
import redis.asyncio as aioredis
from review_service.domain.interfaces.cache_interface import ICacheService


class RedisCacheService(ICacheService):
    """
    Redis implementation of cache service

    Uses async Redis client for non-blocking operations
    Serializes/deserializes data using JSON
    """

    def __init__(self, redis_url: str) -> None:
        """
        Initialize Redis cache service

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection"""
        self.client = await aioredis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            await self.connect()

        try:
            value = await self.client.get(key)
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)
        except json.JSONDecodeError:
            # Return raw value if not JSON
            return value
        except Exception as e:
            # Log error and return None on failure
            print(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if not self.client:
            await self.connect()

        try:
            # Serialize to JSON
            if not isinstance(value, str):
                value = json.dumps(value, default=str)

            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Cache set error for key {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        if not self.client:
            await self.connect()

        try:
            await self.client.delete(key)
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")

    async def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries"""
        if not self.client:
            await self.connect()

        try:
            if pattern:
                # Delete keys matching pattern
                keys = await self.client.keys(pattern)
                if keys:
                    await self.client.delete(*keys)
            else:
                # Clear entire cache
                await self.client.flushdb()
        except Exception as e:
            print(f"Cache clear error for pattern {pattern}: {e}")
