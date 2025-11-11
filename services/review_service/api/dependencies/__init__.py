"""
FastAPI Dependencies
Dependency injection for services, database, cache, etc.
"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from shared.config.settings import get_settings, Settings
from review_service.domain.services.review_service import ReviewService
from review_service.domain.interfaces.review_repository_interface import (
    IReviewRepository,
)
from review_service.domain.interfaces.cache_interface import ICacheService
from review_service.domain.interfaces.event_bus_interface import IEventBus
from review_service.infrastructure.database.postgres_review_repository import (
    PostgresReviewRepository,
)
from review_service.infrastructure.cache.redis_cache import RedisCacheService
from review_service.infrastructure.events.celery_event_bus import CeleryEventBus


# Global instances
settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.debug,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Cache and Event Bus (singletons)
_cache_service: ICacheService = RedisCacheService(settings.redis_url)
_event_bus: IEventBus = CeleryEventBus()  # Using Celery for distributed event processing


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_review_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IReviewRepository:
    """
    Get review repository

    Args:
        session: Database session

    Returns:
        IReviewRepository: Review repository
    """
    return PostgresReviewRepository(session)


async def get_cache_service() -> ICacheService:
    """Get cache service"""
    return _cache_service


async def get_event_bus() -> IEventBus:
    """Get event bus"""
    return _event_bus


async def get_review_service(
    repository: IReviewRepository = Depends(get_review_repository),
    cache: ICacheService = Depends(get_cache_service),
    event_bus: IEventBus = Depends(get_event_bus),
) -> ReviewService:
    """
    Get review service with all dependencies injected

    Args:
        repository: Review repository
        cache: Cache service
        event_bus: Event bus

    Returns:
        ReviewService: Configured review service
    """
    return ReviewService(
        review_repository=repository, cache_service=cache, event_bus=event_bus
    )


async def verify_api_key(
    x_api_key: str = Header(..., alias=settings.api_key_header)
) -> str:
    """
    Verify API key from header

    For now, this is a simple check. In production, verify against database.

    Args:
        x_api_key: API key from header

    Returns:
        str: Verified API key

    Raises:
        HTTPException: If API key is invalid
    """
    # TODO: Implement proper API key validation
    # For development, accept any non-empty key
    if not x_api_key or len(x_api_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key


async def verify_admin_api_key(
    x_api_key: str = Depends(verify_api_key)
) -> str:
    """
    Verify API key has admin privileges

    In production, this would:
    1. Look up the API key in database
    2. Check if key has admin role/permissions
    3. Verify key hasn't expired
    4. Log admin access for audit

    For development: Keys starting with 'admin-' are considered admin keys

    Args:
        x_api_key: Verified API key from verify_api_key dependency

    Returns:
        str: Verified admin API key

    Raises:
        HTTPException: If API key doesn't have admin privileges
    """
    # TODO: Implement proper role-based access control
    # For development, check if key starts with 'admin-'
    if not x_api_key.startswith("admin-"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This operation requires elevated privileges.",
        )

    return x_api_key


def get_settings_dependency() -> Settings:
    """Get application settings"""
    return settings
