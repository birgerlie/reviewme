"""
Platform Service Dependencies
Dependency injection for FastAPI routes
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from shared.database import get_session
from platform_service.domain.services.platform_service import PlatformService
from platform_service.infrastructure.shopify.shopify_client import ShopifyClient
from platform_service.infrastructure.shopify.shopify_auth import ShopifyAuthProvider
from platform_service.infrastructure.shopify.shopify_webhooks import ShopifyWebhookHandler
from platform_service.infrastructure.database.postgres_platform_merchant_repository import (
    PostgresPlatformMerchantRepository,
)
from shared.infrastructure.database.postgres_review_token_repository import (
    PostgresReviewTokenRepository,
)
from review_service.infrastructure.events.celery_event_bus import CeleryEventBus


async def get_platform_merchant_repository(
    session: AsyncSession = Depends(get_session),
) -> PostgresPlatformMerchantRepository:
    """
    Get platform merchant repository

    Args:
        session: Database session

    Returns:
        Repository instance
    """
    return PostgresPlatformMerchantRepository(session)


async def get_review_token_repository(
    session: AsyncSession = Depends(get_session),
) -> PostgresReviewTokenRepository:
    """
    Get review token repository

    Args:
        session: Database session

    Returns:
        Repository instance
    """
    return PostgresReviewTokenRepository(session)


def get_shopify_client(
    platform_merchant_repo: PostgresPlatformMerchantRepository = Depends(
        get_platform_merchant_repository
    ),
) -> ShopifyClient:
    """
    Get Shopify API client

    Args:
        platform_merchant_repo: Repository for fetching access tokens

    Returns:
        Shopify client instance
    """
    return ShopifyClient(merchant_repository=platform_merchant_repo)


def get_shopify_auth_provider() -> ShopifyAuthProvider:
    """
    Get Shopify OAuth provider

    Returns:
        Shopify auth provider instance
    """
    return ShopifyAuthProvider()


def get_shopify_webhook_handler() -> ShopifyWebhookHandler:
    """
    Get Shopify webhook handler

    Returns:
        Shopify webhook handler instance
    """
    return ShopifyWebhookHandler()


def get_event_bus() -> CeleryEventBus:
    """
    Get event bus

    Returns:
        Event bus instance
    """
    return CeleryEventBus()


async def get_platform_service(
    platform_client: ShopifyClient = Depends(get_shopify_client),
    auth_provider: ShopifyAuthProvider = Depends(get_shopify_auth_provider),
    webhook_handler: ShopifyWebhookHandler = Depends(get_shopify_webhook_handler),
    token_repository: PostgresReviewTokenRepository = Depends(get_review_token_repository),
    platform_merchant_repository: PostgresPlatformMerchantRepository = Depends(
        get_platform_merchant_repository
    ),
    event_bus: CeleryEventBus = Depends(get_event_bus),
) -> PlatformService:
    """
    Get platform service with all dependencies injected

    This is the main entry point for platform operations.
    All dependencies are injected here (Dependency Inversion Principle).

    Args:
        platform_client: Platform API client (Shopify, WooCommerce, etc.)
        auth_provider: OAuth provider
        webhook_handler: Webhook handler
        token_repository: Review token repository
        platform_merchant_repository: Platform merchant repository
        event_bus: Event bus for publishing events

    Returns:
        PlatformService instance with all dependencies
    """
    return PlatformService(
        platform_client=platform_client,
        auth_provider=auth_provider,
        webhook_handler=webhook_handler,
        token_repository=token_repository,
        event_bus=event_bus,
        platform_merchant_repository=platform_merchant_repository,
    )
