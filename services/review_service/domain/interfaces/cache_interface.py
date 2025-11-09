"""
Cache Service Interface
Defines the contract for caching operations
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class ICacheService(ABC):
    """
    Abstract base class for cache operations

    Implementations can use Redis, Memcached, or any other cache
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete value from cache

        Args:
            key: Cache key
        """
        pass

    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries

        Args:
            pattern: Optional pattern to match keys (e.g., "product:*")
                     If None, clears all cache
        """
        pass
