"""
Widget Service - Business Logic Layer
Ultra-fast service for serving widget data to public
Performance critical: < 100ms p95 response time
"""
from typing import Dict, Any, Optional
from datetime import datetime

from widget_service.domain.models.widget_config import WidgetConfig
from widget_service.domain.interfaces.widget_repository_interface import (
    IWidgetRepository,
)
from widget_service.domain.interfaces.review_service_client_interface import (
    IReviewServiceClient,
)
from review_service.domain.interfaces.cache_interface import ICacheService


class WidgetService:
    """
    Widget Service

    Performance-critical service that serves widget data to public.

    Business Logic:
    - Heavy caching (10 min TTL for widget data)
    - Returns only enabled widgets
    - Combines config + reviews + rating in single response
    - Optimized for CDN caching

    Performance Requirements:
    - < 100ms p95 response time
    - < 50KB payload size
    - CDN-friendly cache headers
    """

    def __init__(
        self,
        widget_repository: IWidgetRepository,
        review_service_client: IReviewServiceClient,
        cache_service: ICacheService,
    ) -> None:
        """
        Initialize service with dependencies

        Args:
            widget_repository: Repository for widget configs
            review_service_client: Client for review service
            cache_service: Cache for performance
        """
        self.widget_repository = widget_repository
        self.review_service_client = review_service_client
        self.cache_service = cache_service

        # Cache TTL in seconds (10 minutes for widget data)
        self.CACHE_TTL_WIDGET_DATA = 600

    async def get_widget_data(
        self, widget_id: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete widget data (config + reviews + rating)

        This is the main method called by the public widget JavaScript.
        Must be ultra-fast with heavy caching.

        Args:
            widget_id: Widget identifier
            use_cache: Whether to use cache (default: True)

        Returns:
            Dict with config, reviews, and rating data
            None if widget not found

        Raises:
            ValueError: If widget is disabled
        """
        cache_key = f"widget:data:{widget_id}"

        # Try cache first (performance critical!)
        if use_cache:
            cached = await self.cache_service.get(cache_key)
            if cached is not None:
                return cached

        # Get widget configuration
        widget = await self.widget_repository.get_by_id(widget_id)
        if widget is None:
            return None

        # Business Rule: Don't serve disabled widgets
        if not widget.is_enabled():
            raise ValueError(f"Widget {widget_id} is disabled")

        # Fetch reviews and rating from Review Service
        reviews = await self.review_service_client.get_reviews(
            product_id=widget.product_id,
            limit=widget.display_settings.get("reviews_per_page", 10),
            offset=0,
        )

        rating = await self.review_service_client.get_rating(
            product_id=widget.product_id
        )

        # Build response payload
        widget_data = {
            "config": {
                "id": widget.id,
                "layout": widget.layout.value,
                "theme": widget.theme.value,
                "custom_styles": widget.custom_styles,
                "display_settings": widget.display_settings,
            },
            "reviews": reviews,
            "rating": rating,
        }

        # Cache the result (10 minutes)
        if use_cache:
            await self.cache_service.set(
                cache_key, widget_data, self.CACHE_TTL_WIDGET_DATA
            )

        return widget_data

    async def create_widget(self, widget: WidgetConfig) -> WidgetConfig:
        """
        Create a new widget configuration

        Args:
            widget: Widget configuration to create

        Returns:
            Created widget with generated ID
        """
        created_widget = await self.widget_repository.create(widget)
        return created_widget

    async def update_widget(
        self, widget_id: str, updates: Dict[str, Any]
    ) -> WidgetConfig:
        """
        Update widget configuration

        Args:
            widget_id: Widget identifier
            updates: Fields to update

        Returns:
            Updated widget

        Raises:
            ValueError: If widget not found
        """
        # Get existing widget
        widget = await self.widget_repository.get_by_id(widget_id)
        if widget is None:
            raise ValueError(f"Widget {widget_id} not found")

        # Apply updates
        if "enabled" in updates:
            if updates["enabled"]:
                widget.enable()
            else:
                widget.disable()

        if "custom_styles" in updates:
            widget.update_styles(updates["custom_styles"])

        if "display_settings" in updates:
            widget.update_display_settings(updates["display_settings"])

        # Save changes
        updated_widget = await self.widget_repository.update(widget)

        # Invalidate cache
        cache_key = f"widget:data:{widget_id}"
        await self.cache_service.delete(cache_key)

        return updated_widget

    async def get_widget_by_product(
        self, merchant_id: str, product_id: str
    ) -> Optional[WidgetConfig]:
        """
        Get widget configuration by merchant and product

        Args:
            merchant_id: Merchant identifier
            product_id: Product identifier

        Returns:
            Widget configuration if found, None otherwise
        """
        return await self.widget_repository.get_by_merchant_and_product(
            merchant_id, product_id
        )

    async def delete_widget(self, widget_id: str) -> bool:
        """
        Delete a widget configuration

        Args:
            widget_id: Widget identifier

        Returns:
            True if deleted, False if not found
        """
        # Invalidate cache
        cache_key = f"widget:data:{widget_id}"
        await self.cache_service.delete(cache_key)

        # Delete widget
        return await self.widget_repository.delete(widget_id)
