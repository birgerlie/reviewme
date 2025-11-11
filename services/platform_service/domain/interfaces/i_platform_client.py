"""
Platform Client Interface
Defines the contract for platform-specific API interactions
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from platform_service.domain.entities.platform_product import PlatformProduct
from platform_service.domain.entities.platform_order import PlatformOrder


class IPlatformClient(ABC):
    """
    Platform Client Interface

    Defines methods for interacting with e-commerce platform APIs.
    Each platform (Shopify, WooCommerce, etc.) implements this interface,
    allowing the business logic to remain platform-agnostic.

    The key principle: Business logic depends on this interface, not on
    concrete implementations (Dependency Inversion Principle).
    """

    @abstractmethod
    async def get_product(self, merchant_id: str, product_id: str) -> PlatformProduct:
        """
        Get product details from platform

        Args:
            merchant_id: Internal merchant identifier
            product_id: Platform's product ID

        Returns:
            Universal PlatformProduct entity

        Raises:
            ValueError: If product not found
            ConnectionError: If API call fails
        """
        pass

    @abstractmethod
    async def get_order(self, merchant_id: str, order_id: str) -> PlatformOrder:
        """
        Get order details from platform

        Args:
            merchant_id: Internal merchant identifier
            order_id: Platform's order ID

        Returns:
            Universal PlatformOrder entity

        Raises:
            ValueError: If order not found
            ConnectionError: If API call fails
        """
        pass

    @abstractmethod
    async def list_products(
        self, merchant_id: str, limit: int = 50, page: int = 1
    ) -> List[PlatformProduct]:
        """
        List products from platform

        Args:
            merchant_id: Internal merchant identifier
            limit: Maximum products to return
            page: Page number for pagination

        Returns:
            List of universal PlatformProduct entities

        Raises:
            ConnectionError: If API call fails
        """
        pass

    @abstractmethod
    async def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify webhook signature for security

        Each platform has different webhook verification mechanisms:
        - Shopify: HMAC-SHA256 signature
        - WooCommerce: Secret validation
        - BigCommerce: OAuth signature

        Args:
            payload: Raw webhook payload (bytes)
            headers: HTTP headers from webhook request

        Returns:
            True if webhook is authentic, False otherwise
        """
        pass
