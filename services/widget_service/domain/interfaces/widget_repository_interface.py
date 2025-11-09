"""
Widget Repository Interface
Defines the contract for widget configuration data access
"""
from abc import ABC, abstractmethod
from typing import Optional
from widget_service.domain.models.widget_config import WidgetConfig


class IWidgetRepository(ABC):
    """
    Abstract base class for Widget Repository

    This interface defines all data access operations for widget configurations.
    """

    @abstractmethod
    async def create(self, widget: WidgetConfig) -> WidgetConfig:
        """
        Create a new widget configuration

        Args:
            widget: Widget configuration to create

        Returns:
            WidgetConfig: Created widget with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, widget_id: str) -> Optional[WidgetConfig]:
        """
        Get widget configuration by ID

        Args:
            widget_id: Widget identifier

        Returns:
            Optional[WidgetConfig]: Widget if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_merchant_and_product(
        self, merchant_id: str, product_id: str
    ) -> Optional[WidgetConfig]:
        """
        Get widget configuration by merchant and product

        Args:
            merchant_id: Merchant identifier
            product_id: Product identifier

        Returns:
            Optional[WidgetConfig]: Widget if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, widget: WidgetConfig) -> WidgetConfig:
        """
        Update an existing widget configuration

        Args:
            widget: Widget with updated fields

        Returns:
            WidgetConfig: Updated widget
        """
        pass

    @abstractmethod
    async def delete(self, widget_id: str) -> bool:
        """
        Delete a widget configuration

        Args:
            widget_id: Widget identifier

        Returns:
            bool: True if deleted, False if not found
        """
        pass
