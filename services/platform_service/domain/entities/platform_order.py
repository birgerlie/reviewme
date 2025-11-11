"""
Platform Order Entity
Universal order representation across all e-commerce platforms
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class PlatformOrderLineItem:
    """
    Order line item (product in an order)
    """
    product_id: str
    product_title: str
    variant_id: Optional[str] = None
    variant_title: Optional[str] = None
    quantity: int = 1
    price: float = 0.0
    currency: str = "USD"


@dataclass
class PlatformOrder:
    """
    Platform Order Entity

    Universal representation of an order across different e-commerce platforms.
    Used to trigger review requests after order fulfillment.
    """

    # Core identification
    id: Optional[str] = None
    merchant_id: str = ""
    platform_order_id: str = ""  # Platform's internal order ID
    platform_order_number: str = ""  # Human-readable order number (e.g., "#1001")

    # Customer Information
    customer_email: str = ""
    customer_name: Optional[str] = None

    # Order Details
    line_items: List[PlatformOrderLineItem] = field(default_factory=list)
    total: float = 0.0
    currency: str = "USD"

    # Fulfillment Status
    fulfilled: bool = False
    fulfilled_at: Optional[datetime] = None

    # Timestamps
    created_at: Optional[datetime] = None

    # Escape hatch for platform-specific data
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate order data

        Raises:
            ValueError: If validation fails
        """
        if not self.merchant_id:
            raise ValueError("merchant_id is required")

        if not self.platform_order_id:
            raise ValueError("platform_order_id is required")

        if not self.customer_email or "@" not in self.customer_email:
            raise ValueError("valid customer_email is required")

        if not self.line_items:
            raise ValueError("at least one line item is required")

        if self.total < 0:
            raise ValueError("total must be non-negative")

    def get_product_ids(self) -> List[str]:
        """Get list of all product IDs in the order"""
        return [item.product_id for item in self.line_items]

    def is_fulfilled(self) -> bool:
        """Check if order is fulfilled"""
        return self.fulfilled

    def __repr__(self) -> str:
        return (
            f"PlatformOrder(id={self.id}, merchant_id={self.merchant_id}, "
            f"platform_order_id={self.platform_order_id}, "
            f"customer={self.customer_email}, fulfilled={self.fulfilled})"
        )
