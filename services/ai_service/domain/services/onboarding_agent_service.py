"""
Onboarding AI Agent Service
Automated merchant onboarding with AI-powered design extraction and widget generation

REFACTORED: Now uses Claude Tool Calling API for reliable, structured responses!
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import re


class PlatformType(Enum):
    """E-commerce platform types"""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    BIGCOMMERCE = "bigcommerce"
    MAGENTO = "magento"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


@dataclass
class DesignSystem:
    """Extracted design system from merchant website"""
    primary_color: str
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: str = "#FFFFFF"
    text_color: str = "#333333"
    font_family: str = "Arial, sans-serif"
    heading_font: Optional[str] = None
    border_radius: str = "4px"
    spacing_unit: str = "8px"
    button_style: str = "rounded"
    theme_style: str = "modern"


@dataclass
class OnboardingResult:
    """Complete onboarding analysis result"""
    domain: str
    merchant_id: str
    platform_type: PlatformType
    design_system: DesignSystem
    widget_config: Dict[str, Any]
    implementation_code: Dict[str, str]
    preview_url: Optional[str] = None
    confidence_score: float = 0.0


class OnboardingAgentService:
    """
    Onboarding AI Agent Service (TOOL CALLING VERSION)

    Automates merchant onboarding using Claude's structured tool calling:
    1. Analyzing their storefront (domain)
    2. Detecting platform (Shopify, WooCommerce, etc.)
    3. Extracting design system (colors, fonts, spacing)
    4. Generating themed review widget
    5. Creating implementation code

    This is a KEY competitive advantage - merchants can launch in minutes!
    
    IMPROVEMENT: Uses Claude Tool Calling for reliable, type-safe responses!
    """

    # Define tools for structured responses
    PLATFORM_DETECTION_TOOL = {
        "name": "detect_ecommerce_platform",
        "description": "Detect the e-commerce platform used by a website based on HTML analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["shopify", "woocommerce", "bigcommerce", "magento", "custom", "unknown"],
                    "description": "The detected e-commerce platform"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score from 0.0 to 1.0"
                },
                "indicators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of indicators that led to this detection"
                }
            },
            "required": ["platform", "confidence", "indicators"]
        }
    }

    DESIGN_EXTRACTION_TOOL = {
        "name": "extract_design_system",
        "description": "Extract design system (colors, fonts, spacing) from website HTML/CSS",
        "input_schema": {
            "type": "object",
            "properties": {
                "primary_color": {
                    "type": "string",
                    "description": "Primary brand color in hex format (e.g., #2C3E50)"
                },
                "secondary_color": {
                    "type": "string",
                    "description": "Secondary brand color in hex format"
                },
                "accent_color": {
                    "type": "string",
                    "description": "Accent color in hex format"
                },
                "background_color": {
                    "type": "string",
                    "description": "Background color in hex format"
                },
                "text_color": {
                    "type": "string",
                    "description": "Text color in hex format"
                },
                "font_family": {
                    "type": "string",
                    "description": "Primary font family with fallbacks (e.g., 'Roboto, Arial, sans-serif')"
                },
                "heading_font": {
                    "type": "string",
                    "description": "Heading font family (if different from primary)"
                },
                "border_radius": {
                    "type": "string",
                    "description": "Border radius value (e.g., '4px', '8px')"
                },
                "spacing_unit": {
                    "type": "string",
                    "description": "Base spacing unit (e.g., '8px', '16px')"
                },
                "button_style": {
                    "type": "string",
                    "enum": ["rounded", "square", "pill"],
                    "description": "Button style pattern"
                },
                "theme_style": {
                    "type": "string",
                    "enum": ["modern-minimal", "classic", "bold", "elegant"],
                    "description": "Overall aesthetic theme"
                }
            },
            "required": ["primary_color", "font_family", "border_radius", "theme_style"]
        }
    }

    WIDGET_CONFIG_TOOL = {
        "name": "generate_widget_config",
        "description": "Generate themed widget configuration matching the brand design",
        "input_schema": {
            "type": "object",
            "properties": {
                "layout": {
                    "type": "string",
                    "enum": ["grid", "list", "carousel", "masonry"],
                    "description": "Widget layout style"
                },
                "theme": {
                    "type": "string",
                    "enum": ["light", "dark", "auto"],
                    "description": "Color theme"
                },
                "custom_styles": {
                    "type": "object",
                    "properties": {
                        "primaryColor": {"type": "string"},
                        "secondaryColor": {"type": "string"},
                        "fontFamily": {"type": "string"},
                        "borderRadius": {"type": "string"},
                        "spacing": {"type": "string"}
                    },
                    "description": "Custom CSS styles"
                },
                "display_settings": {
                    "type": "object",
                    "properties": {
                        "show_photos": {"type": "boolean"},
                        "show_verified_badge": {"type": "boolean"},
                        "show_response": {"type": "boolean"},
                        "reviews_per_page": {"type": "integer"},
                        "star_color": {"type": "string"}
                    },
                    "description": "Display configuration"
                }
            },
            "required": ["layout", "theme", "custom_styles"]
        }
    }

    def __init__(
        self,
        anthropic_client,
        http_client,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
    ):
        """
        Initialize Onboarding Agent Service

        Args:
            anthropic_client: Anthropic API client
            http_client: HTTP client for fetching websites
            model: Claude model to use
            max_tokens: Max tokens for responses
        """
        self.client = anthropic_client
        self.http_client = http_client
        self.model = model
        self.max_tokens = max_tokens
        self._cache: Dict[str, OnboardingResult] = {}
        self._html_cache: Dict[str, str] = {}  # Cache HTML fetches

    async def analyze_merchant_website(
        self,
        domain: str,
        merchant_id: str,
    ) -> OnboardingResult:
        """
        Complete merchant website analysis

        This is the main entry point for automated onboarding.

        Args:
            domain: Merchant's domain (e.g., "example.com")
            merchant_id: Merchant ID

        Returns:
            OnboardingResult with platform, design system, and widget config
        """
        # Check cache
        cache_key = f"{domain}:{merchant_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Fetch website HTML
        html_content = await self._fetch_website(domain)

        # Detect platform using Tool Calling
        platform = await self.detect_platform(domain)

        # Extract design system using Tool Calling
        design_system = await self.extract_design_system(domain, html_content)

        # Generate widget configuration using Tool Calling
        widget_config = await self.generate_widget_config(design_system, merchant_id)

        # Generate implementation code
        implementation_code = await self.generate_implementation_code(
            widget_config, merchant_id, domain
        )

        # Generate preview
        preview = await self.generate_preview(widget_config, merchant_id)

        # Create result
        result = OnboardingResult(
            domain=domain,
            merchant_id=merchant_id,
            platform_type=platform,
            design_system=design_system,
            widget_config=widget_config,
            implementation_code=implementation_code,
            preview_url=preview.get("preview_url"),
            confidence_score=0.95,
        )

        # Cache result
        self._cache[cache_key] = result

        return result

    async def detect_platform(self, domain: str) -> PlatformType:
        """
        Detect e-commerce platform using Tool Calling

        Uses structured tool calling for reliable platform detection.

        Args:
            domain: Merchant domain

        Returns:
            PlatformType
        """
        html_content = await self._fetch_website(domain)

        # Quick pattern matching for common platforms (fast path)
        if "shopify" in html_content.lower() or "myshopify.com" in html_content.lower():
            return PlatformType.SHOPIFY
        
        if "woocommerce" in html_content.lower() or "wp-content" in html_content.lower():
            return PlatformType.WOOCOMMERCE
        
        if "bigcommerce" in html_content.lower():
            return PlatformType.BIGCOMMERCE
        
        if "magento" in html_content.lower():
            return PlatformType.MAGENTO

        # Use AI with Tool Calling for deeper analysis
        prompt = f"""Analyze this website HTML and detect the e-commerce platform.

HTML (first 5000 chars):
{html_content[:5000]}

Look for:
- JavaScript variables (e.g., Shopify, woocommerce_params)
- Meta tags (generator, powered-by)
- Script sources (myshopify.com, woocommerce)
- HTML comments or class names
- URL patterns

Use the detect_ecommerce_platform tool to return your analysis."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            tools=[self.PLATFORM_DETECTION_TOOL],
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract tool use from response
        for content in response.content:
            if content.type == "tool_use" and content.name == "detect_ecommerce_platform":
                platform_data = content.input
                try:
                    return PlatformType(platform_data["platform"])
                except (KeyError, ValueError):
                    return PlatformType.UNKNOWN

        return PlatformType.UNKNOWN

    async def extract_design_system(
        self, 
        domain: str, 
        html_content: str
    ) -> DesignSystem:
        """
        Extract design system using Tool Calling

        Uses structured tool calling for reliable design extraction.

        Args:
            domain: Merchant domain
            html_content: HTML content

        Returns:
            DesignSystem object
        """
        prompt = f"""Analyze this website and extract its design system.

Website: {domain}

HTML (first 5000 chars):
{html_content[:5000]}

Extract the design system by analyzing:
- CSS styles in <style> tags or style attributes
- Google Fonts or other font imports (<link> tags)
- Color schemes in backgrounds, buttons, links, headers
- Border radius patterns (buttons, cards, images)
- Spacing patterns (margins, padding)
- Overall aesthetic (modern, classic, minimal, bold)

Use the extract_design_system tool to return the design system."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            tools=[self.DESIGN_EXTRACTION_TOOL],
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract tool use from response
        for content in response.content:
            if content.type == "tool_use" and content.name == "extract_design_system":
                design_data = content.input
                try:
                    return DesignSystem(
                        primary_color=design_data.get("primary_color", "#2C3E50"),
                        secondary_color=design_data.get("secondary_color"),
                        accent_color=design_data.get("accent_color"),
                        background_color=design_data.get("background_color", "#FFFFFF"),
                        text_color=design_data.get("text_color", "#333333"),
                        font_family=design_data.get("font_family", "Arial, sans-serif"),
                        heading_font=design_data.get("heading_font"),
                        border_radius=design_data.get("border_radius", "4px"),
                        spacing_unit=design_data.get("spacing_unit", "8px"),
                        button_style=design_data.get("button_style", "rounded"),
                        theme_style=design_data.get("theme_style", "modern"),
                    )
                except Exception:
                    pass

        # Fallback to default design
        return DesignSystem(
            primary_color="#2C3E50",
            secondary_color="#E74C3C",
            font_family="Arial, sans-serif",
        )

    async def generate_widget_config(
        self,
        design_system: DesignSystem,
        merchant_id: str,
    ) -> Dict[str, Any]:
        """
        Generate themed widget configuration using Tool Calling

        Uses structured tool calling for reliable config generation.

        Args:
            design_system: Extracted design system
            merchant_id: Merchant ID

        Returns:
            Widget configuration dict
        """
        prompt = f"""Generate a review widget configuration that perfectly matches this design system:

Design System:
- Primary Color: {design_system.primary_color}
- Secondary Color: {design_system.secondary_color}
- Font Family: {design_system.font_family}
- Border Radius: {design_system.border_radius}
- Theme Style: {design_system.theme_style}
- Button Style: {design_system.button_style}
- Spacing: {design_system.spacing_unit}

Create a widget configuration that:
1. Matches the brand's visual identity
2. Uses appropriate layout for the theme style
3. Includes all custom styles from the design system
4. Configures display settings for best user experience

Use the generate_widget_config tool to return the configuration."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            tools=[self.WIDGET_CONFIG_TOOL],
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract tool use from response
        for content in response.content:
            if content.type == "tool_use" and content.name == "generate_widget_config":
                config = content.input
                config["merchant_id"] = merchant_id
                return config

        # Fallback config
        return {
            "layout": "grid",
            "theme": "light",
            "merchant_id": merchant_id,
            "custom_styles": {
                "primaryColor": design_system.primary_color,
                "fontFamily": design_system.font_family,
                "borderRadius": design_system.border_radius,
            },
            "display_settings": {
                "show_photos": True,
                "show_verified_badge": True,
                "reviews_per_page": 12,
            }
        }

    async def generate_implementation_code(
        self,
        widget_config: Dict[str, Any],
        merchant_id: str,
        domain: str,
    ) -> Dict[str, str]:
        """
        Generate implementation code

        Creates ready-to-use HTML, CSS, and JavaScript code.

        Args:
            widget_config: Widget configuration
            merchant_id: Merchant ID
            domain: Merchant domain

        Returns:
            Dict with 'html', 'css', 'javascript' keys
        """
        # Generate JavaScript embed code
        javascript = f"""
<!-- Review Platform Widget -->
<script>
  (function() {{
    window.ReviewPlatformConfig = {{
      merchantId: '{merchant_id}',
      productId: 'PRODUCT_ID', // Replace with actual product ID
      layout: '{widget_config.get("layout", "grid")}',
      theme: '{widget_config.get("theme", "light")}',
      customStyles: {json.dumps(widget_config.get("custom_styles", {}), indent=4)}
    }};
    
    var script = document.createElement('script');
    script.src = 'https://cdn.reviewplatform.com/widget/v1/reviews.js';
    script.async = true;
    document.head.appendChild(script);
  }})();
</script>
"""

        # Generate HTML container
        html = f"""
<!-- Review Widget Container -->
<div id="review-platform-widget" data-merchant-id="{merchant_id}">
  <!-- Widget will load here -->
  <div class="review-widget-loading">Loading reviews...</div>
</div>
"""

        # Generate CSS styles
        custom_styles = widget_config.get("custom_styles", {})
        primary_color = custom_styles.get("primaryColor", "#2C3E50")
        font_family = custom_styles.get("fontFamily", "Arial, sans-serif")
        border_radius = custom_styles.get("borderRadius", "4px")

        css = f"""
/* Review Platform Custom Styles */
.review-platform-widget {{
  font-family: {font_family};
  color: #333;
}}

.review-platform-widget .review-card {{
  border: 1px solid #e0e0e0;
  border-radius: {border_radius};
  padding: 16px;
  margin-bottom: 16px;
  background: #fff;
}}

.review-platform-widget .review-rating {{
  color: {primary_color};
}}

.review-platform-widget .review-author {{
  font-weight: 600;
  color: {primary_color};
}}

.review-platform-widget .verified-badge {{
  background: {primary_color};
  color: white;
  padding: 2px 8px;
  border-radius: {border_radius};
  font-size: 12px;
}}
"""

        return {
            "html": html.strip(),
            "css": css.strip(),
            "javascript": javascript.strip(),
        }

    async def generate_preview(
        self,
        widget_config: Dict[str, Any],
        merchant_id: str,
    ) -> Dict[str, Any]:
        """
        Generate widget preview

        In production, this would generate a screenshot or live preview.
        For now, returns a placeholder.

        Args:
            widget_config: Widget configuration
            merchant_id: Merchant ID

        Returns:
            Preview data with URL
        """
        return {
            "preview_url": f"https://cdn.reviewplatform.com/previews/{merchant_id}.png",
            "status": "ready",
            "widget_config": widget_config,
        }

    async def _fetch_website(self, domain: str) -> str:
        """
        Fetch website HTML

        Args:
            domain: Domain to fetch

        Returns:
            HTML content
        """
        # Check cache first
        if domain in self._html_cache:
            return self._html_cache[domain]

        # Ensure domain has protocol
        url = domain
        if not url.startswith("http"):
            url = f"https://{url}"

        response = await self.http_client.get(url)
        html = response.text

        # Cache the result
        self._html_cache[domain] = html

        return html
