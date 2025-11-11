"""
Platform Merchant Entity
Universal merchant representation across all e-commerce platforms
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class PlatformType(Enum):
    """Supported e-commerce platforms"""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    BIGCOMMERCE = "bigcommerce"
    CUSTOM = "custom"


@dataclass
class PlatformMerchant:
    """
    Platform Merchant Entity

    Universal representation of a merchant across different e-commerce platforms.
    This abstraction allows the system to work with any platform without
    platform-specific code in the business logic.

    The platform_metadata field provides an "escape hatch" for platform-specific
    data that doesn't fit the universal model.
    """

    # Core identification
    id: Optional[str] = None
    platform: PlatformType = PlatformType.SHOPIFY
    platform_domain: str = ""  # e.g., "mystore.myshopify.com"
    platform_merchant_id: str = ""  # Platform's internal merchant ID

    # Authentication & Authorization
    access_token: str = ""
    scopes: List[str] = field(default_factory=list)
    token_expires_at: Optional[datetime] = None

    # Store Information
    store_name: str = ""
    email: str = ""
    currency: str = "USD"
    timezone: str = "UTC"

    # Status & Configuration
    installed_at: Optional[datetime] = None
    active: bool = True
    widget_config: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Escape hatch for platform-specific data
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate platform merchant data

        Raises:
            ValueError: If validation fails
        """
        if not self.platform_domain:
            raise ValueError("platform_domain is required")

        if not self.platform_merchant_id:
            raise ValueError("platform_merchant_id is required")

        if not self.access_token:
            raise ValueError("access_token is required")

        if not self.store_name:
            raise ValueError("store_name is required")

        if not self.email or "@" not in self.email:
            raise ValueError("valid email is required")

    def is_token_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.token_expires_at:
            return False  # No expiration set
        return datetime.utcnow() >= self.token_expires_at

    def deactivate(self, current_time: Optional[datetime] = None) -> None:
        """Deactivate merchant (app uninstalled)"""
        self.active = False
        self.updated_at = current_time or datetime.utcnow()

    def activate(self, current_time: Optional[datetime] = None) -> None:
        """Activate merchant"""
        self.active = True
        self.updated_at = current_time or datetime.utcnow()

    def update_widget_config(self, config: Dict[str, Any], current_time: Optional[datetime] = None) -> None:
        """Update widget configuration"""
        self.widget_config.update(config)
        self.updated_at = current_time or datetime.utcnow()

    def __repr__(self) -> str:
        return (
            f"PlatformMerchant(id={self.id}, platform={self.platform.value}, "
            f"domain={self.platform_domain}, active={self.active})"
        )
