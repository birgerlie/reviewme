"""
Onboarding API Routes
Automated merchant onboarding with AI agent
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ai_service.domain.services.onboarding_agent_service import (
    OnboardingAgentService,
    OnboardingResult,
    PlatformType,
)

router = APIRouter(tags=["onboarding"])


class AnalyzeWebsiteRequest(BaseModel):
    """Request model for website analysis"""
    domain: str
    merchant_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "merchant_id": "merchant_123",
            }
        }


class AnalyzeWebsiteResponse(BaseModel):
    """Response model for website analysis"""
    domain: str
    merchant_id: str
    platform_type: str
    design_system: Dict[str, Any]
    widget_config: Dict[str, Any]
    implementation_code: Dict[str, str]
    preview_url: Optional[str]
    confidence_score: float

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "merchant_id": "merchant_123",
                "platform_type": "shopify",
                "design_system": {
                    "primary_color": "#2C3E50",
                    "font_family": "Helvetica Neue, Arial, sans-serif",
                },
                "widget_config": {
                    "layout": "grid",
                    "theme": "light",
                },
                "implementation_code": {
                    "html": "<!-- widget HTML -->",
                    "css": "/* widget styles */",
                    "javascript": "// widget script",
                },
                "preview_url": "https://cdn.reviewplatform.com/previews/merchant_123.png",
                "confidence_score": 0.95,
            }
        }


# Mock dependency (to be replaced with real implementation)
async def get_onboarding_agent() -> OnboardingAgentService:
    """Dependency: Get onboarding agent service"""
    from unittest.mock import Mock, AsyncMock
    import httpx

    # Create a real async HTTP client
    http_client = httpx.AsyncClient()
    
    # Mock Anthropic client
    mock_client = Mock()
    mock_client.messages.create = AsyncMock()
    
    return OnboardingAgentService(
        anthropic_client=mock_client,
        http_client=http_client,
    )


@router.post(
    "/api/v1/onboarding/analyze",
    response_model=AnalyzeWebsiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze merchant website (AI-powered onboarding)",
    description="Automatically analyze a merchant's website and generate themed review widget",
)
async def analyze_website(
    request: AnalyzeWebsiteRequest,
    agent: OnboardingAgentService = Depends(get_onboarding_agent),
) -> AnalyzeWebsiteResponse:
    """
    AI-Powered Merchant Onboarding

    This endpoint is a **KEY competitive advantage**!

    **What it does:**
    1. Fetches the merchant's website
    2. Detects e-commerce platform (Shopify, WooCommerce, etc.)
    3. Extracts design system (colors, fonts, spacing)
    4. Generates themed review widget configuration
    5. Creates ready-to-use implementation code

    **Merchants can launch in minutes instead of hours!**

    **Process:**
    - Crawls website HTML/CSS
    - Uses Claude AI to analyze design
    - Generates perfectly themed widget
    - Returns HTML/CSS/JS code to embed

    **Example use case:**
    ```
    POST /api/v1/onboarding/analyze
    {
      "domain": "mystore.com",
      "merchant_id": "merchant_123"
    }
    ```

    Returns complete widget config + implementation code!
    """
    try:
        result = await agent.analyze_merchant_website(
            domain=request.domain,
            merchant_id=request.merchant_id,
        )

        return AnalyzeWebsiteResponse(
            domain=result.domain,
            merchant_id=result.merchant_id,
            platform_type=result.platform_type.value,
            design_system={
                "primary_color": result.design_system.primary_color,
                "secondary_color": result.design_system.secondary_color,
                "accent_color": result.design_system.accent_color,
                "background_color": result.design_system.background_color,
                "text_color": result.design_system.text_color,
                "font_family": result.design_system.font_family,
                "heading_font": result.design_system.heading_font,
                "border_radius": result.design_system.border_radius,
                "spacing_unit": result.design_system.spacing_unit,
                "button_style": result.design_system.button_style,
                "theme_style": result.design_system.theme_style,
            },
            widget_config=result.widget_config,
            implementation_code=result.implementation_code,
            preview_url=result.preview_url,
            confidence_score=result.confidence_score,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze website: {str(e)}",
        )


@router.get(
    "/api/v1/onboarding/platforms",
    summary="List supported e-commerce platforms",
    description="Get list of supported e-commerce platforms for auto-detection",
)
async def list_platforms():
    """
    List supported platforms

    Returns all e-commerce platforms we can auto-detect.
    """
    return {
        "platforms": [
            {
                "type": "shopify",
                "name": "Shopify",
                "auto_detect": True,
                "integration_available": True,
            },
            {
                "type": "woocommerce",
                "name": "WooCommerce",
                "auto_detect": True,
                "integration_available": True,
            },
            {
                "type": "bigcommerce",
                "name": "BigCommerce",
                "auto_detect": True,
                "integration_available": False,
            },
            {
                "type": "magento",
                "name": "Magento",
                "auto_detect": True,
                "integration_available": False,
            },
            {
                "type": "custom",
                "name": "Custom/Other",
                "auto_detect": False,
                "integration_available": False,
            },
        ]
    }
