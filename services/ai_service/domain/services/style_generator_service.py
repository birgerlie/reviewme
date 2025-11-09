"""
AI-Powered Style Generator Service
Uses Anthropic Claude to generate matching widget styles
This is the unique differentiator for the platform
"""
import json
import hashlib
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic

from shared.config.settings import get_settings


class StyleGeneratorService:
    """
    AI-Powered Style Generator

    Uses Claude to analyze brand websites and generate matching
    widget styles automatically. This is the key differentiator
    that makes widget integration seamless.

    Business Value:
    - Reduces setup time from hours to seconds
    - Ensures brand consistency automatically
    - Unique feature competitors don't have
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize service with Anthropic API key

        Args:
            api_key: Anthropic API key (optional, uses settings if not provided)
        """
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.client = AsyncAnthropic(api_key=self.api_key)
        self._cache: Dict[str, Any] = {}

    async def generate_widget_style(
        self,
        brand_website_url: str,
        brand_colors: Optional[Dict[str, str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        include_responsive: bool = False,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate widget style configuration based on brand

        Args:
            brand_website_url: URL of the brand's website
            brand_colors: Optional brand color palette
            preferences: Optional user preferences (layout, theme, etc.)
            include_responsive: Whether to include responsive breakpoints
            use_cache: Whether to use cached results

        Returns:
            Dict containing style configuration (colors, typography, spacing, etc.)

        Raises:
            ValueError: If Claude returns invalid JSON
        """
        # Check cache
        cache_key = self._generate_cache_key(
            brand_website_url, brand_colors, preferences
        )
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        # Build prompt
        prompt = self._build_style_generation_prompt(
            brand_website_url, brand_colors, preferences, include_responsive
        )

        # Call Claude API
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        try:
            style_config = json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Claude: {e}")

        # Cache result
        if use_cache:
            self._cache[cache_key] = style_config

        return style_config

    async def generate_css_from_config(self, config: Dict[str, Any]) -> str:
        """
        Generate CSS from style configuration

        Args:
            config: Style configuration dictionary

        Returns:
            str: Generated CSS code
        """
        prompt = f"""Generate clean, production-ready CSS for a review widget based on this configuration:

Configuration:
{json.dumps(config, indent=2)}

Requirements:
- Use CSS custom properties (variables) for colors
- Include all necessary selectors (.review-widget, .review-card, .star-rating, etc.)
- Make it responsive
- Follow BEM naming convention
- Include hover states
- Optimize for performance
- Keep bundle size small

Return ONLY the CSS code, no explanations."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip()

    async def analyze_brand_style(self, html_content: str) -> Dict[str, Any]:
        """
        Analyze brand style from HTML content

        Args:
            html_content: HTML content from brand website

        Returns:
            Dict containing extracted style information
        """
        prompt = f"""Analyze this website HTML and extract the brand's style guide:

HTML:
{html_content[:5000]}  # Limit to avoid token limits

Extract and return a JSON object with:
- colors: primary, secondary, accent, text colors
- typography: font families, sizes, weights
- spacing: padding, margins
- borders: radius, widths
- shadows: if present

Return ONLY valid JSON, no explanations."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _build_style_generation_prompt(
        self,
        brand_website_url: str,
        brand_colors: Optional[Dict[str, str]],
        preferences: Optional[Dict[str, Any]],
        include_responsive: bool,
    ) -> str:
        """Build prompt for style generation"""
        prompt = f"""You are an expert UI/UX designer. Generate a complete style configuration for a review widget that matches the brand at {brand_website_url}.

"""

        if brand_colors:
            prompt += f"""Brand Colors Provided:
{json.dumps(brand_colors, indent=2)}

Use these colors in the design.
"""

        if preferences:
            prompt += f"""User Preferences:
{json.dumps(preferences, indent=2)}

Incorporate these preferences.
"""

        prompt += """
Generate a comprehensive style configuration as a JSON object with:

{
  "colors": {
    "primary": "#hexcolor",
    "secondary": "#hexcolor",
    "accent": "#hexcolor",
    "text": "#hexcolor",
    "background": "#hexcolor",
    "border": "#hexcolor"
  },
  "typography": {
    "fontFamily": "font stack",
    "fontSize": "16px",
    "lineHeight": "1.5",
    "fontWeightNormal": "400",
    "fontWeightBold": "700"
  },
  "spacing": {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px"
  },
  "borders": {
    "radius": "8px",
    "width": "1px"
  },
  "shadows": {
    "sm": "box-shadow value",
    "md": "box-shadow value",
    "lg": "box-shadow value"
  }
"""

        if include_responsive:
            prompt += """,
  "breakpoints": {
    "mobile": "768px",
    "tablet": "1024px",
    "desktop": "1280px"
  }
"""

        if preferences and "layout" in preferences:
            prompt += f""",
  "layout": "{preferences['layout']}"
"""

        prompt += """
}

Requirements:
- Make it look modern and professional
- Ensure good contrast for accessibility (WCAG AA)
- Match the brand's visual identity
- Keep it clean and minimal
- Optimize for performance

Return ONLY valid JSON, no explanations or markdown."""

        return prompt

    def _generate_cache_key(
        self,
        url: str,
        colors: Optional[Dict[str, str]],
        preferences: Optional[Dict[str, Any]],
    ) -> str:
        """Generate cache key from inputs"""
        key_parts = [url]
        if colors:
            key_parts.append(json.dumps(colors, sort_keys=True))
        if preferences:
            key_parts.append(json.dumps(preferences, sort_keys=True))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear the style generation cache"""
        self._cache.clear()
