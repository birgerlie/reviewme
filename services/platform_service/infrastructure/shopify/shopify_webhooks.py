"""
Shopify Webhook Handler
Manages webhook registration, parsing, and verification
"""
import hmac
import hashlib
import base64
from typing import List, Dict, Any
import httpx

from platform_service.domain.interfaces.i_webhook_handler import IWebhookHandler
from shared.config.settings import get_settings


class ShopifyWebhookHandler(IWebhookHandler):
    """
    Shopify Webhook Handler

    Manages Shopify webhooks for real-time event notifications:
    - orders/fulfilled → Trigger review request
    - app/uninstalled → Clean up merchant data

    Security:
    - All webhooks verified with HMAC-SHA256
    - Base64-encoded signatures

    References:
    https://shopify.dev/docs/apps/webhooks
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Initialize webhook handler

        Args:
            api_key: Shopify API key
            api_secret: Shopify API secret (for HMAC verification)
        """
        settings = get_settings()
        self.api_key = api_key or settings.shopify_api_key
        self.api_secret = api_secret or settings.shopify_api_secret
        self.api_version = "2024-01"

        # Webhook topics we care about
        self.webhook_topics = [
            "orders/fulfilled",  # Order fulfilled → Send review request
            "app/uninstalled",  # App uninstalled → Clean up data
        ]

    async def register_webhooks(
        self, merchant_id: str, access_token: str, webhook_url: str
    ) -> List[str]:
        """
        Register webhooks with Shopify

        Args:
            merchant_id: Internal merchant ID (not used for Shopify API)
            access_token: Shopify access token
            webhook_url: Base URL for webhooks (e.g., "https://api.example.com/webhooks/shopify")

        Returns:
            List of webhook IDs created

        Raises:
            ConnectionError: If API call fails
        """
        # Extract shop domain from merchant (would come from repository)
        # For now, we'll need to get it from the merchant
        # This is a simplified version - in production, get from merchant_repository

        webhook_ids = []

        for topic in self.webhook_topics:
            # Create webhook for this topic
            webhook_data = {
                "webhook": {
                    "topic": topic,
                    "address": f"{webhook_url}/{topic.replace('/', '_')}",
                    "format": "json",
                }
            }

            # We need the shop domain, but we don't have it in this method signature
            # This would need to be passed or retrieved from merchant_repository
            # For now, leaving as TODO - this will be fixed when we integrate with repositories

            # Placeholder for webhook ID
            webhook_ids.append(f"webhook_{topic.replace('/', '_')}")

        return webhook_ids

    async def parse_webhook_event(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Parse Shopify webhook into universal format

        Args:
            payload: Webhook payload (JSON)
            headers: HTTP headers

        Returns:
            Universal event dictionary:
            {
                "event_type": "order.fulfilled" | "app.uninstalled",
                "merchant_id": "...",  # Extracted from shop domain
                "shop_domain": "...",
                "data": {...}  # Event-specific data
            }

        Raises:
            ValueError: If payload is invalid
        """
        # Get topic from header
        topic = headers.get("X-Shopify-Topic", "")
        shop_domain = headers.get("X-Shopify-Shop-Domain", "")

        if not topic:
            raise ValueError("Missing X-Shopify-Topic header")

        if not shop_domain:
            raise ValueError("Missing X-Shopify-Shop-Domain header")

        # Transform topic to universal event type
        event_type_map = {
            "orders/fulfilled": "order.fulfilled",
            "app/uninstalled": "app.uninstalled",
        }

        event_type = event_type_map.get(topic, topic)

        # Parse based on event type
        if topic == "orders/fulfilled":
            return self._parse_order_fulfilled(payload, shop_domain, event_type)
        elif topic == "app/uninstalled":
            return self._parse_app_uninstalled(payload, shop_domain, event_type)
        else:
            # Unknown event type - return as-is
            return {
                "event_type": event_type,
                "shop_domain": shop_domain,
                "merchant_id": None,  # Will be resolved by service layer
                "data": payload,
            }

    def _parse_order_fulfilled(
        self, payload: Dict[str, Any], shop_domain: str, event_type: str
    ) -> Dict[str, Any]:
        """Parse orders/fulfilled webhook"""
        order = payload

        # Extract relevant order data
        line_items = []
        for item in order.get("line_items", []):
            line_items.append(
                {
                    "product_id": str(item.get("product_id", "")),
                    "variant_id": str(item.get("variant_id", "")),
                    "title": item.get("title", ""),
                    "quantity": item.get("quantity", 1),
                }
            )

        return {
            "event_type": event_type,
            "shop_domain": shop_domain,
            "merchant_id": None,  # Resolved by service layer from shop_domain
            "data": {
                "order_id": str(order.get("id", "")),
                "order_number": order.get("name", ""),
                "customer_email": order.get("customer", {}).get("email", ""),
                "customer_name": f"{order.get('customer', {}).get('first_name', '')} {order.get('customer', {}).get('last_name', '')}".strip(),
                "line_items": line_items,
                "total": float(order.get("total_price", 0)),
                "currency": order.get("currency", "USD"),
                "fulfilled_at": order.get("fulfilled_at"),
                "created_at": order.get("created_at"),
            },
        }

    def _parse_app_uninstalled(
        self, payload: Dict[str, Any], shop_domain: str, event_type: str
    ) -> Dict[str, Any]:
        """Parse app/uninstalled webhook"""
        return {
            "event_type": event_type,
            "shop_domain": shop_domain,
            "merchant_id": None,  # Resolved by service layer
            "data": {
                "shop_id": str(payload.get("id", "")),
                "shop_domain": shop_domain,
                "uninstalled_at": payload.get("updated_at"),
            },
        }

    async def delete_webhooks(
        self, merchant_id: str, webhook_ids: List[str], access_token: str
    ) -> bool:
        """
        Delete webhooks from Shopify

        Args:
            merchant_id: Internal merchant ID
            webhook_ids: List of Shopify webhook IDs
            access_token: Shopify access token

        Returns:
            True if all deleted successfully

        Raises:
            ConnectionError: If API call fails
        """
        # Similar to register_webhooks, we need shop domain
        # This would be retrieved from merchant_repository in production

        # For each webhook ID, make DELETE request
        # DELETE /admin/api/2024-01/webhooks/{webhook_id}.json

        # Placeholder for now
        return True

    def get_webhook_topics(self) -> List[str]:
        """
        Get list of supported webhook topics

        Returns:
            List of Shopify webhook topics
        """
        return self.webhook_topics

    def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify Shopify webhook HMAC signature

        Shopify signs webhooks with HMAC-SHA256 and base64 encoding

        Args:
            payload: Raw webhook payload (bytes)
            headers: HTTP headers

        Returns:
            True if signature is valid, False otherwise
        """
        # Get HMAC from header
        hmac_header = headers.get("X-Shopify-Hmac-Sha256", "")
        if not hmac_header:
            return False

        # Compute HMAC-SHA256
        computed_hmac = hmac.new(
            self.api_secret.encode("utf-8"), payload, hashlib.sha256
        ).digest()

        # Base64 encode
        computed_hmac_b64 = base64.b64encode(computed_hmac).decode("utf-8")

        # Constant-time comparison
        return hmac.compare_digest(computed_hmac_b64, hmac_header)
