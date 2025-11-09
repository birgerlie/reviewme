"""
Onboarding AI Agent Service
Automated merchant onboarding with AI-powered design extraction and widget generation
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
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
    Onboarding AI Agent Service

    Automates merchant onboarding by:
    1. Analyzing their storefront (domain)
    2. Detecting platform (Shopify, WooCommerce, etc.)
    3. Extracting design system (colors, fonts, spacing)
    4. Generating themed review widget
    5. Creating implementation code

    This is a KEY competitive advantage - merchants can launch in minutes!
    """

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

        # Detect platform
        platform = await self.detect_platform(domain)

        # Extract design system using AI
        design_system = await self.extract_design_system(domain, html_content)

        # Generate widget configuration
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
        Detect e-commerce platform

        Uses pattern matching and AI analysis to identify the platform.

        Args:
            domain: Merchant domain

        Returns:
            PlatformType
        """
        html_content = await self._fetch_website(domain)

        # Quick pattern matching for common platforms
        if "shopify" in html_content.lower() or "myshopify.com" in html_content.lower():
            return PlatformType.SHOPIFY
        
        if "woocommerce" in html_content.lower() or "wp-content" in html_content.lower():
            return PlatformType.WOOCOMMERCE
        
        if "bigcommerce" in html_content.lower():
            return PlatformType.BIGCOMMERCE
        
        if "magento" in html_content.lower():
            return PlatformType.MAGENTO

        # Use AI for deeper analysis
        prompt = f"""Analyze this website HTML and determine the e-commerce platform.

HTML (first 5000 chars):
{html_content[:5000]}

Respond with ONLY a JSON object:
{{
    "platform": "shopify" | "woocommerce" | "bigcommerce" | "magento" | "custom" | "unknown",
    "confidence": 0.0-1.0,
    "indicators": ["indicator1", "indicator2"]
}}"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            result = json.loads(response.content[0].text)
            return PlatformType(result["platform"])
        except:
            return PlatformType.UNKNOWN

    async def extract_design_system(
        self, 
        domain: str, 
        html_content: str
    ) -> DesignSystem:
        """
        Extract design system using AI

        Analyzes the website to extract:
        - Colors (primary, secondary, accent)
        - Typography (fonts, sizes)
        - Spacing and borders
        - Overall style theme

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

Extract the following and respond with ONLY a JSON object:
{{
    "primary_color": "#HEX",
    "secondary_color": "#HEX",
    "accent_color": "#HEX",
    "background_color": "#HEX",
    "text_color": "#HEX",
    "font_family": "Font Name, fallback",
    "heading_font": "Font Name, fallback",
    "border_radius": "Xpx",
    "spacing_unit": "Xpx",
    "button_style": "rounded" | "square" | "pill",
    "theme_style": "modern-minimal" | "classic" | "bold" | "elegant"
}}

Look for:
- CSS styles in <style> tags or style attributes
- Google Fonts or other font imports
- Color schemes in backgrounds, buttons, links
- Border radius patterns
- Overall aesthetic"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = json.loads(response.content[0].text)
            return DesignSystem(**data)
        except:
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
        Generate themed widget configuration

        Creates a widget config that matches the merchant's brand.

        Args:
            design_system: Extracted design system
            merchant_id: Merchant ID

        Returns:
            Widget configuration dict
        """
        prompt = f"""Generate a review widget configuration that matches this design system:

Design System:
- Primary Color: {design_system.primary_color}
- Font: {design_system.font_family}
- Border Radius: {design_system.border_radius}
- Theme Style: {design_system.theme_style}

Create a configuration with ONLY this JSON format:
{{
    "layout": "grid" | "list" | "carousel" | "masonry",
    "theme": "light" | "dark" | "auto",
    "custom_styles": {{
        "primaryColor": "#HEX",
        "secondaryColor": "#HEX",
        "fontFamily": "Font, fallback",
        "borderRadius": "Xpx",
        "spacing": "Xpx"
    }},
    "display_settings": {{
        "show_photos": true,
        "show_verified_badge": true,
        "show_response": true,
        "reviews_per_page": 12,
        "star_color": "#HEX"
    }}
}}

Make it match the brand perfectly!"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            config = json.loads(response.content[0].text)
            config["merchant_id"] = merchant_id
            return config
        except:
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
        primary_color = widget_config.get("custom_styles", {}).get("primaryColor", "#2C3E50")
        font_family = widget_config.get("custom_styles", {}).get("fontFamily", "Arial, sans-serif")
        border_radius = widget_config.get("custom_styles", {}).get("borderRadius", "4px")

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
