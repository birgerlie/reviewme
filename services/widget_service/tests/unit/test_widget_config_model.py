"""
Test Widget Configuration domain model
Following TDD: Write tests first
"""
import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from widget_service.domain.models.widget_config import (
    WidgetConfig,
    WidgetLayout,
    WidgetTheme,
)


class TestWidgetConfigModel:
    """Test Widget Configuration domain model"""

    def test_create_widget_config_with_required_fields(self) -> None:
        """GIVEN valid config data WHEN creating WidgetConfig THEN should succeed"""
        config = WidgetConfig(
            id="widget_123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.GRID,
            theme=WidgetTheme.LIGHT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert config.merchant_id == "merchant_456"
        assert config.product_id == "prod_789"
        assert config.layout == WidgetLayout.GRID
        assert config.theme == WidgetTheme.LIGHT

    def test_widget_config_with_custom_styles(self) -> None:
        """GIVEN custom style config WHEN creating widget THEN styles are stored"""
        custom_styles = {
            "colors": {"primary": "#FF0000", "secondary": "#00FF00"},
            "typography": {"fontFamily": "Arial"},
        }

        config = WidgetConfig(
            id="widget_123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.LIST,
            theme=WidgetTheme.CUSTOM,
            custom_styles=custom_styles,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert config.custom_styles == custom_styles
        assert config.theme == WidgetTheme.CUSTOM

    def test_widget_config_enable_disable(self) -> None:
        """GIVEN widget config WHEN enable/disable called THEN updates enabled status"""
        config = WidgetConfig(
            id="widget_123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.CAROUSEL,
            theme=WidgetTheme.DARK,
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert config.enabled is True

        config.disable()
        assert config.enabled is False

        config.enable()
        assert config.enabled is True

    def test_widget_config_with_display_settings(self) -> None:
        """GIVEN display settings WHEN creating widget THEN settings are stored"""
        display_settings = {
            "show_verified_badge": True,
            "show_photos": True,
            "show_date": False,
            "reviews_per_page": 10,
            "sort_by": "date_desc",
        }

        config = WidgetConfig(
            id="widget_123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.GRID,
            theme=WidgetTheme.LIGHT,
            display_settings=display_settings,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert config.display_settings["show_verified_badge"] is True
        assert config.display_settings["reviews_per_page"] == 10

    def test_all_layout_types_are_valid(self) -> None:
        """GIVEN all layout enum values WHEN used THEN all are valid"""
        assert WidgetLayout.GRID.value == "grid"
        assert WidgetLayout.LIST.value == "list"
        assert WidgetLayout.CAROUSEL.value == "carousel"
        assert WidgetLayout.MASONRY.value == "masonry"

    def test_all_theme_types_are_valid(self) -> None:
        """GIVEN all theme enum values WHEN used THEN all are valid"""
        assert WidgetTheme.LIGHT.value == "light"
        assert WidgetTheme.DARK.value == "dark"
        assert WidgetTheme.AUTO.value == "auto"
        assert WidgetTheme.CUSTOM.value == "custom"

    def test_widget_config_update_styles(self) -> None:
        """GIVEN widget config WHEN update_styles called THEN styles are updated"""
        config = WidgetConfig(
            id="widget_123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.GRID,
            theme=WidgetTheme.LIGHT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        new_styles = {"colors": {"primary": "#0000FF"}}
        config.update_styles(new_styles)

        assert config.custom_styles == new_styles
        assert config.theme == WidgetTheme.CUSTOM

    def test_widget_config_with_cdn_url(self) -> None:
        """GIVEN widget config WHEN created THEN CDN URL can be generated"""
        config = WidgetConfig(
            id="widget_abc123",
            merchant_id="merchant_456",
            product_id="prod_789",
            layout=WidgetLayout.GRID,
            theme=WidgetTheme.LIGHT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        cdn_url = config.get_cdn_url()
        assert "widget_abc123" in cdn_url
        assert isinstance(cdn_url, str)
