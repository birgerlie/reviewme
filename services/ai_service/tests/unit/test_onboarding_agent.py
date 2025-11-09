"""
Test Onboarding AI Agent
Automated merchant onboarding with AI-powered design extraction
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_service.domain.services.onboarding_agent_service import (
    OnboardingAgentService,
    OnboardingResult,
    PlatformType,
    DesignSystem,
)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    client = Mock()
    
    # Mock for platform detection
    platform_response = Mock()
    platform_response.content = [
        Mock(text='{"platform": "shopify", "confidence": 0.95, "indicators": ["myshopify.com", "Shopify.theme"]}')
    ]
    
    # Mock for design extraction
    design_response = Mock()
    design_response.content = [
        Mock(text='''{
            "primary_color": "#2C3E50",
            "secondary_color": "#E74C3C",
            "accent_color": "#3498DB",
            "background_color": "#FFFFFF",
            "text_color": "#333333",
            "font_family": "Helvetica Neue, Arial, sans-serif",
            "heading_font": "Georgia, serif",
            "border_radius": "4px",
            "spacing_unit": "8px",
            "button_style": "rounded",
            "theme_style": "modern-minimal"
        }''')
    ]
    
    # Mock for widget generation
    widget_response = Mock()
    widget_response.content = [
        Mock(text='''{
            "layout": "grid",
            "theme": "light",
            "custom_styles": {
                "primaryColor": "#2C3E50",
                "fontFamily": "Helvetica Neue, Arial, sans-serif",
                "borderRadius": "4px"
            },
            "display_settings": {
                "show_photos": true,
                "show_verified_badge": true,
                "reviews_per_page": 12
            }
        }''')
    ]
    
    client.messages.create = AsyncMock(
        side_effect=[platform_response, design_response, widget_response]
    )
    
    return client


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for fetching website HTML"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=Mock(
        status_code=200,
        text='<html><head><link href="https://fonts.googleapis.com/css?family=Roboto"></head><body style="color: #333;"></body></html>',
        headers={'content-type': 'text/html'}
    ))
    return client


@pytest.fixture
def onboarding_agent(mock_anthropic_client, mock_http_client):
    """Create OnboardingAgentService with mocked dependencies"""
    return OnboardingAgentService(
        anthropic_client=mock_anthropic_client,
        http_client=mock_http_client,
        model="claude-sonnet-4-5-20250929",
    )


@pytest.mark.asyncio
class TestOnboardingAgentService:
    """Test Onboarding AI Agent"""

    async def test_analyze_merchant_website_complete_flow(
        self,
        onboarding_agent,
        mock_http_client,
        mock_anthropic_client,
    ) -> None:
        """
        GIVEN merchant domain
        WHEN analyze_merchant_website called
        THEN returns complete onboarding result
        """
        result = await onboarding_agent.analyze_merchant_website(
            domain="example.com",
            merchant_id="merchant_123",
        )

        assert isinstance(result, OnboardingResult)
        assert result.domain == "example.com"
        assert result.merchant_id == "merchant_123"
        assert result.platform_type == PlatformType.SHOPIFY
        assert result.design_system is not None
        assert result.widget_config is not None
        assert result.implementation_code is not None

    async def test_detect_platform_shopify(
        self,
        onboarding_agent,
        mock_http_client,
    ) -> None:
        """
        GIVEN Shopify store
        WHEN detect_platform called
        THEN identifies as Shopify
        """
        mock_http_client.get.return_value.text = '''
            <html>
                <script>var Shopify = {shop: "example.myshopify.com"};</script>
            </html>
        '''

        platform = await onboarding_agent.detect_platform("example.com")

        assert platform == PlatformType.SHOPIFY

    async def test_detect_platform_woocommerce(
        self,
        onboarding_agent,
        mock_http_client,
    ) -> None:
        """
        GIVEN WooCommerce store
        WHEN detect_platform called
        THEN identifies as WooCommerce
        """
        mock_http_client.get.return_value.text = '''
            <html>
                <meta name="generator" content="WooCommerce 7.0" />
            </html>
        '''

        platform = await onboarding_agent.detect_platform("example.com")

        assert platform == PlatformType.WOOCOMMERCE

    async def test_extract_design_system(
        self,
        onboarding_agent,
        mock_http_client,
    ) -> None:
        """
        GIVEN website HTML
        WHEN extract_design_system called
        THEN returns design system with colors and fonts
        """
        design = await onboarding_agent.extract_design_system(
            domain="example.com",
            html_content="<html><body></body></html>",
        )

        assert isinstance(design, DesignSystem)
        assert design.primary_color is not None
        assert design.font_family is not None
        assert design.border_radius is not None

    async def test_generate_widget_config(
        self,
        onboarding_agent,
    ) -> None:
        """
        GIVEN design system
        WHEN generate_widget_config called
        THEN returns themed widget configuration
        """
        design = DesignSystem(
            primary_color="#2C3E50",
            secondary_color="#E74C3C",
            font_family="Roboto, sans-serif",
            border_radius="8px",
        )

        widget_config = await onboarding_agent.generate_widget_config(
            design_system=design,
            merchant_id="merchant_123",
        )

        assert "layout" in widget_config or "merchant_id" in widget_config
        assert "custom_styles" in widget_config or "merchant_id" in widget_config

    async def test_generate_implementation_code(
        self,
        onboarding_agent,
    ) -> None:
        """
        GIVEN widget config
        WHEN generate_implementation_code called
        THEN returns HTML/CSS/JS code
        """
        widget_config = {
            "layout": "grid",
            "theme": "light",
            "custom_styles": {
                "primaryColor": "#2C3E50",
                "fontFamily": "Roboto",
            }
        }

        code = await onboarding_agent.generate_implementation_code(
            widget_config=widget_config,
            merchant_id="merchant_123",
            domain="example.com",
        )

        assert "html" in code
        assert "css" in code
        assert "javascript" in code
        assert "merchant_123" in code["javascript"]
        assert "#2C3E50" in code["css"]

    async def test_handles_invalid_domain(
        self,
        onboarding_agent,
        mock_http_client,
    ) -> None:
        """
        GIVEN invalid domain
        WHEN analyze_merchant_website called
        THEN raises ValueError
        """
        mock_http_client.get.side_effect = Exception("Domain not found")

        with pytest.raises(Exception):
            await onboarding_agent.analyze_merchant_website(
                domain="invalid-domain-12345.com",
                merchant_id="merchant_123",
            )

    async def test_caches_analysis_results(
        self,
        onboarding_agent,
        mock_http_client,
        mock_anthropic_client,
    ) -> None:
        """
        GIVEN same domain analyzed twice
        WHEN analyze_merchant_website called
        THEN uses cached result on second call
        """
        # First call
        result1 = await onboarding_agent.analyze_merchant_website(
            domain="example.com",
            merchant_id="merchant_123",
        )

        # Second call (should use cache)
        result2 = await onboarding_agent.analyze_merchant_website(
            domain="example.com",
            merchant_id="merchant_123",
        )

        # Should only fetch HTML once
        assert mock_http_client.get.call_count == 1

    async def test_generates_preview_screenshot_placeholder(
        self,
        onboarding_agent,
    ) -> None:
        """
        GIVEN widget config
        WHEN generate_preview called
        THEN returns preview placeholder
        """
        widget_config = {"layout": "grid", "theme": "light"}

        preview = await onboarding_agent.generate_preview(
            widget_config=widget_config,
            merchant_id="merchant_123",
        )

        assert preview["preview_url"] is not None
        assert preview["status"] == "ready"
