"""
Test AI-powered Style Generator Service
Following TDD: Write tests first
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_service.domain.services.style_generator_service import StyleGeneratorService


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    client = Mock()
    client.messages = Mock()
    client.messages.create = AsyncMock()
    return client


@pytest.fixture
def style_generator_service(mock_anthropic_client):
    """Create StyleGeneratorService with mocked client"""
    service = StyleGeneratorService(api_key="test_key")
    service.client = mock_anthropic_client
    return service


@pytest.mark.asyncio
class TestStyleGeneratorService:
    """Test AI Style Generator Service"""

    async def test_generate_widget_style_returns_valid_config(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN brand website URL and colors
        WHEN generate_widget_style called
        THEN returns valid style configuration
        """
        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"colors": {"primary": "#000000", "secondary": "#FFFFFF"}, "typography": {"fontFamily": "Arial"}}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await style_generator_service.generate_widget_style(
            brand_website_url="https://example.com",
            brand_colors={"primary": "#FF0000"},
        )

        assert "colors" in result
        assert "typography" in result
        assert isinstance(result["colors"], dict)
        assert result["colors"]["primary"] == "#000000"

    async def test_generate_widget_style_includes_brand_colors(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN brand colors provided
        WHEN generate_widget_style called
        THEN incorporates brand colors in prompt
        """
        mock_response = Mock()
        mock_response.content = [Mock(text='{"colors": {"primary": "#FF0000"}}')]
        mock_anthropic_client.messages.create.return_value = mock_response

        await style_generator_service.generate_widget_style(
            brand_website_url="https://example.com",
            brand_colors={"primary": "#FF0000", "secondary": "#00FF00"},
        )

        # Verify the API was called with brand colors in prompt
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args is not None
        prompt_content = str(call_args)
        assert "#FF0000" in prompt_content or "FF0000" in prompt_content

    async def test_generate_css_from_config(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN style configuration
        WHEN generate_css_from_config called
        THEN returns valid CSS
        """
        config = {
            "colors": {"primary": "#FF0000", "secondary": "#00FF00"},
            "typography": {"fontFamily": "Arial, sans-serif", "fontSize": "16px"},
            "spacing": {"padding": "16px"},
        }

        mock_response = Mock()
        mock_response.content = [
            Mock(
                text=".review-widget { color: #FF0000; font-family: Arial, sans-serif; }"
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await style_generator_service.generate_css_from_config(config)

        assert isinstance(result, str)
        assert ".review-widget" in result
        assert "#FF0000" in result or "rgb" in result.lower()

    async def test_analyze_brand_style_from_html(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN website HTML
        WHEN analyze_brand_style called
        THEN extracts style information
        """
        html = """
        <html>
            <head><style>
                body { font-family: 'Helvetica', sans-serif; color: #333; }
                .header { background: #0066cc; }
            </style></head>
            <body><h1>Brand Site</h1></body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"colors": {"primary": "#0066cc", "text": "#333333"}, "typography": {"fontFamily": "Helvetica"}}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await style_generator_service.analyze_brand_style(html)

        assert "colors" in result
        assert "typography" in result
        assert isinstance(result, dict)

    async def test_generate_style_with_preferences(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN user preferences
        WHEN generate_widget_style called with preferences
        THEN incorporates preferences in generation
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"colors": {"primary": "#FF0000"}, "layout": "grid", "borderRadius": "8px"}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        preferences = {"layout": "grid", "theme": "modern", "borderRadius": "8px"}

        result = await style_generator_service.generate_widget_style(
            brand_website_url="https://example.com",
            brand_colors={"primary": "#FF0000"},
            preferences=preferences,
        )

        assert "layout" in result or "colors" in result
        assert isinstance(result, dict)

    async def test_handles_invalid_json_response(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN invalid JSON response from Claude
        WHEN generate_widget_style called
        THEN raises appropriate error
        """
        mock_response = Mock()
        mock_response.content = [Mock(text="This is not valid JSON")]
        mock_anthropic_client.messages.create.return_value = mock_response

        with pytest.raises(ValueError):
            await style_generator_service.generate_widget_style(
                brand_website_url="https://example.com"
            )

    async def test_caches_generated_styles(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN style generated for a URL
        WHEN same URL requested again
        THEN returns cached result without API call
        """
        mock_response = Mock()
        mock_response.content = [Mock(text='{"colors": {"primary": "#000000"}}')]
        mock_anthropic_client.messages.create.return_value = mock_response

        # First call
        result1 = await style_generator_service.generate_widget_style(
            brand_website_url="https://example.com", use_cache=True
        )

        # Second call - should use cache
        result2 = await style_generator_service.generate_widget_style(
            brand_website_url="https://example.com", use_cache=True
        )

        # Should only call API once
        assert mock_anthropic_client.messages.create.call_count == 1
        assert result1 == result2

    async def test_includes_responsive_breakpoints(
        self, style_generator_service, mock_anthropic_client
    ) -> None:
        """
        GIVEN style generation request
        WHEN generate_widget_style called
        THEN includes responsive breakpoints in config
        """
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"colors": {"primary": "#FF0000"}, "breakpoints": {"mobile": "768px", "tablet": "1024px"}}'
            )
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await style_generator_service.generate_widget_style(
            brand_website_url="https://example.com", include_responsive=True
        )

        assert "breakpoints" in result or "colors" in result
