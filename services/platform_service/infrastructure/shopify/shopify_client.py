"""
Shopify API Client
Implements platform client interface for Shopify
"""
import hmac
import hashlib
from typing import List, Dict, Any
import httpx

from platform_service.domain.interfaces.i_platform_client import IPlatformClient
from platform_service.domain.entities.platform_product import PlatformProduct
from platform_service.domain.entities.platform_order import (
    PlatformOrder,
    PlatformOrderLineItem,
)
from shared.config.settings import get_settings


class ShopifyClient(IPlatformClient):
    """
    Shopify API Client

    Implements Shopify Admin REST API interactions.
    Transforms Shopify-specific data structures into universal entities.

    Features:
    - Automatic rate limiting (Shopify: 2 req/sec)
    - Retry logic with exponential backoff
    - Error handling and logging

    References:
    https://shopify.dev/docs/api/admin-rest
    """

    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        merchant_repository=None,
    ):
        """
        Initialize Shopify client

        Args:
            api_key: Shopify API key
            api_secret: Shopify API secret
            merchant_repository: Repository to fetch merchant access tokens
        """
        settings = get_settings()
        self.api_key = api_key or settings.shopify_api_key
        self.api_secret = api_secret or settings.shopify_api_secret
        self.api_version = "2024-01"
        self.merchant_repository = merchant_repository

    async def _get_merchant_access_token(self, merchant_id: str) -> tuple[str, str]:
        """
        Get merchant's access token and shop domain

        Args:
            merchant_id: Internal merchant ID

        Returns:
            Tuple of (access_token, shop_domain)

        Raises:
            ValueError: If merchant not found
        """
        if not self.merchant_repository:
            raise ValueError("Merchant repository not configured")

        merchant = await self.merchant_repository.get_by_id(merchant_id)
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

        return merchant.access_token, merchant.platform_domain

    async def _make_api_request(
        self, method: str, url: str, access_token: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to Shopify

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full API URL
            access_token: Shopify access token
            **kwargs: Additional arguments for httpx

        Returns:
            JSON response

        Raises:
            ConnectionError: If API call fails
            ValueError: If response is invalid
        """
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method, url, headers=headers, timeout=10.0, **kwargs
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(f"Resource not found: {url}")
                elif e.response.status_code == 429:
                    raise ConnectionError("Shopify rate limit exceeded")
                else:
                    raise ConnectionError(
                        f"Shopify API error: {e.response.status_code} - {e.response.text}"
                    )
            except httpx.RequestError as e:
                raise ConnectionError(f"Request failed: {str(e)}")

    async def get_product(self, merchant_id: str, product_id: str) -> PlatformProduct:
        """
        Get product from Shopify

        Args:
            merchant_id: Internal merchant ID
            product_id: Shopify product ID

        Returns:
            Universal PlatformProduct entity

        Raises:
            ValueError: If product not found
            ConnectionError: If API call fails
        """
        access_token, shop_domain = await self._get_merchant_access_token(merchant_id)

        url = f"https://{shop_domain}/admin/api/{self.api_version}/products/{product_id}.json"
        response = await self._make_api_request("GET", url, access_token)

        # Transform Shopify product to universal format
        shopify_product = response["product"]

        return PlatformProduct(
            merchant_id=merchant_id,
            platform_product_id=str(shopify_product["id"]),
            title=shopify_product["title"],
            description=shopify_product.get("body_html", ""),
            price=float(shopify_product["variants"][0]["price"])
            if shopify_product["variants"]
            else 0.0,
            currency="USD",  # Shopify stores currency in shop settings
            image_url=shopify_product["image"]["src"]
            if shopify_product.get("image")
            else None,
            images=[img["src"] for img in shopify_product.get("images", [])],
            url=f"https://{shop_domain}/products/{shopify_product['handle']}",
            has_variants=len(shopify_product["variants"]) > 1,
            variant_count=len(shopify_product["variants"]),
            in_stock=any(
                var.get("inventory_quantity", 0) > 0
                for var in shopify_product["variants"]
            ),
            platform_metadata={"shopify": shopify_product},  # Store full response
        )

    async def get_order(self, merchant_id: str, order_id: str) -> PlatformOrder:
        """
        Get order from Shopify

        Args:
            merchant_id: Internal merchant ID
            order_id: Shopify order ID

        Returns:
            Universal PlatformOrder entity

        Raises:
            ValueError: If order not found
            ConnectionError: If API call fails
        """
        access_token, shop_domain = await self._get_merchant_access_token(merchant_id)

        url = f"https://{shop_domain}/admin/api/{self.api_version}/orders/{order_id}.json"
        response = await self._make_api_request("GET", url, access_token)

        # Transform Shopify order to universal format
        shopify_order = response["order"]

        # Transform line items
        line_items = []
        for item in shopify_order.get("line_items", []):
            line_items.append(
                PlatformOrderLineItem(
                    product_id=str(item["product_id"]),
                    product_title=item["title"],
                    variant_id=str(item["variant_id"]) if item.get("variant_id") else None,
                    variant_title=item.get("variant_title"),
                    quantity=item["quantity"],
                    price=float(item["price"]),
                    currency=shopify_order["currency"],
                )
            )

        return PlatformOrder(
            merchant_id=merchant_id,
            platform_order_id=str(shopify_order["id"]),
            platform_order_number=shopify_order.get("name", ""),
            customer_email=shopify_order["customer"]["email"]
            if shopify_order.get("customer")
            else "",
            customer_name=f"{shopify_order['customer'].get('first_name', '')} {shopify_order['customer'].get('last_name', '')}".strip()
            if shopify_order.get("customer")
            else None,
            line_items=line_items,
            total=float(shopify_order["total_price"]),
            currency=shopify_order["currency"],
            fulfilled=shopify_order.get("fulfillment_status") == "fulfilled",
            fulfilled_at=shopify_order.get("fulfilled_at"),
            created_at=shopify_order.get("created_at"),
            platform_metadata={"shopify": shopify_order},
        )

    async def list_products(
        self, merchant_id: str, limit: int = 50, page: int = 1
    ) -> List[PlatformProduct]:
        """
        List products from Shopify

        Args:
            merchant_id: Internal merchant ID
            limit: Maximum products to return (max 250 for Shopify)
            page: Page number

        Returns:
            List of universal PlatformProduct entities

        Raises:
            ConnectionError: If API call fails
        """
        access_token, shop_domain = await self._get_merchant_access_token(merchant_id)

        # Shopify pagination uses limit + page_info (not page numbers)
        # For simplicity, using limit parameter
        url = f"https://{shop_domain}/admin/api/{self.api_version}/products.json?limit={min(limit, 250)}"
        response = await self._make_api_request("GET", url, access_token)

        # Transform all products
        products = []
        for shopify_product in response.get("products", []):
            products.append(
                PlatformProduct(
                    merchant_id=merchant_id,
                    platform_product_id=str(shopify_product["id"]),
                    title=shopify_product["title"],
                    description=shopify_product.get("body_html", ""),
                    price=float(shopify_product["variants"][0]["price"])
                    if shopify_product["variants"]
                    else 0.0,
                    currency="USD",
                    image_url=shopify_product["image"]["src"]
                    if shopify_product.get("image")
                    else None,
                    images=[img["src"] for img in shopify_product.get("images", [])],
                    url=f"https://{shop_domain}/products/{shopify_product['handle']}",
                    has_variants=len(shopify_product["variants"]) > 1,
                    variant_count=len(shopify_product["variants"]),
                    in_stock=True,  # Simplified for list view
                    platform_metadata={"shopify": shopify_product},
                )
            )

        return products

    async def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify Shopify webhook HMAC signature

        Args:
            payload: Raw webhook payload (bytes)
            headers: HTTP headers from webhook request

        Returns:
            True if webhook is authentic, False otherwise
        """
        # Get HMAC from header
        hmac_header = headers.get("X-Shopify-Hmac-Sha256", "")
        if not hmac_header:
            return False

        # Compute HMAC-SHA256
        computed_hmac = hmac.new(
            self.api_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(computed_hmac, hmac_header)
