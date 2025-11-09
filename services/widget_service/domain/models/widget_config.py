"""
Widget Configuration domain model
Represents the configuration for an embeddable review widget
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class WidgetLayout(Enum):
    """Widget layout types"""

    GRID = "grid"
    LIST = "list"
    CAROUSEL = "carousel"
    MASONRY = "masonry"


class WidgetTheme(Enum):
    """Widget theme types"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"


@dataclass
class WidgetConfig:
    """
    Widget Configuration domain model

    Represents configuration for an embeddable review widget.
    Supports multiple layouts, themes, and customization options.

    Business Rules:
    - Each merchant can have multiple widgets (different products/pages)
    - Custom styles automatically set theme to CUSTOM
    - Widgets can be enabled/disabled without deletion
    - CDN URLs are generated for performance
    """

    # Required fields
    merchant_id: str
    product_id: str
    layout: WidgetLayout
    theme: WidgetTheme
    created_at: datetime
    updated_at: datetime

    # Optional fields
    id: Optional[str] = None
    enabled: bool = True
    custom_styles: Dict[str, Any] = field(default_factory=dict)
    display_settings: Dict[str, Any] = field(default_factory=dict)

    def enable(self) -> None:
        """Enable the widget"""
        self.enabled = True
        self.updated_at = datetime.utcnow()

    def disable(self) -> None:
        """Disable the widget"""
        self.enabled = False
        self.updated_at = datetime.utcnow()

    def update_styles(self, new_styles: Dict[str, Any]) -> None:
        """
        Update widget custom styles

        Args:
            new_styles: New style configuration

        Business Rule: Setting custom styles changes theme to CUSTOM
        """
        self.custom_styles = new_styles
        self.theme = WidgetTheme.CUSTOM
        self.updated_at = datetime.utcnow()

    def update_display_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update widget display settings

        Args:
            settings: New display settings
        """
        self.display_settings.update(settings)
        self.updated_at = datetime.utcnow()

    def get_cdn_url(self, base_url: str = "https://cdn.reviewplatform.com") -> str:
        """
        Generate CDN URL for widget JavaScript

        Args:
            base_url: CDN base URL

        Returns:
            str: Full CDN URL for this widget
        """
        return f"{base_url}/widget/{self.id}.js"

    def is_enabled(self) -> bool:
        """Check if widget is enabled"""
        return self.enabled

    def __repr__(self) -> str:
        return (
            f"WidgetConfig(id={self.id}, merchant_id={self.merchant_id}, "
            f"product_id={self.product_id}, layout={self.layout.value}, "
            f"enabled={self.enabled})"
        )
