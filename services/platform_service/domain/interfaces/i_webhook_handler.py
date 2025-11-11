"""
Webhook Handler Interface
Defines the contract for platform webhook management
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IWebhookHandler(ABC):
    """
    Webhook Handler Interface

    Defines methods for registering, parsing, and managing platform webhooks.
    Webhooks enable real-time updates when events occur on the platform
    (e.g., order fulfilled, app uninstalled).

    Key webhooks we care about:
    - orders/fulfilled → Trigger review request email
    - app/uninstalled → Clean up merchant data
    """

    @abstractmethod
    async def register_webhooks(
        self, merchant_id: str, access_token: str, webhook_url: str
    ) -> List[str]:
        """
        Register webhooks with platform

        Called after merchant installs the app to set up event listeners

        Args:
            merchant_id: Internal merchant identifier
            access_token: Platform OAuth token
            webhook_url: Our webhook endpoint URL

        Returns:
            List of webhook IDs created (for cleanup later)

        Raises:
            ConnectionError: If API call fails
        """
        pass

    @abstractmethod
    async def parse_webhook_event(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Parse webhook payload into universal format

        Different platforms send different webhook structures.
        This method transforms them into a universal format.

        Args:
            payload: Webhook payload (JSON)
            headers: HTTP headers

        Returns:
            Universal event dictionary with:
            {
                "event_type": "order.fulfilled" | "app.uninstalled",
                "merchant_id": "...",
                "data": {...}  # Event-specific data
            }

        Raises:
            ValueError: If payload is invalid
        """
        pass

    @abstractmethod
    async def delete_webhooks(
        self, merchant_id: str, webhook_ids: List[str], access_token: str
    ) -> bool:
        """
        Delete webhooks from platform

        Called when merchant uninstalls the app

        Args:
            merchant_id: Internal merchant identifier
            webhook_ids: List of webhook IDs to delete
            access_token: Platform OAuth token

        Returns:
            True if all deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_webhook_topics(self) -> List[str]:
        """
        Get list of webhook topics this handler supports

        Returns:
            List of supported webhook topics

        Example:
            ["orders/fulfilled", "orders/cancelled", "app/uninstalled"]
        """
        pass
