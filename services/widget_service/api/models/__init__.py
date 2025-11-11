"""
API Models for Widget Service
Pydantic schemas for request/response
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class WidgetDataResponse(BaseModel):
    """Response model for widget data (public endpoint)"""

    config: Dict[str, Any] = Field(..., description="Widget configuration")
    reviews: List[Dict[str, Any]] = Field(..., description="Product reviews")
    rating: Dict[str, Any] = Field(..., description="Rating summary")

    class Config:
        json_schema_extra = {
            "example": {
                "config": {
                    "id": "widget_123",
                    "layout": "grid",
                    "theme": "light",
                    "custom_styles": {},
                    "display_settings": {"reviews_per_page": 10},
                },
                "reviews": [
                    {
                        "id": "rev_1",
                        "rating": 5,
                        "title": "Great!",
                        "content": "Excellent product",
                    }
                ],
                "rating": {"average_rating": 4.5, "total_reviews": 100},
            }
        }


class WidgetConfigCreateRequest(BaseModel):
    """Request model for creating widget configuration"""

    merchant_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    layout: str = Field(default="grid", pattern="^(grid|list|carousel|masonry)$")
    theme: str = Field(default="light", pattern="^(light|dark|auto|custom)$")
    custom_styles: Dict[str, Any] = Field(default_factory=dict)
    display_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "merchant_123",
                "product_id": "prod_456",
                "layout": "grid",
                "theme": "light",
                "display_settings": {"reviews_per_page": 10, "show_photos": True},
            }
        }


class WidgetConfigResponse(BaseModel):
    """Response model for widget configuration"""

    id: str
    merchant_id: str
    product_id: str
    layout: str
    theme: str
    enabled: bool
    custom_styles: Dict[str, Any]
    display_settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    cdn_url: str

    class Config:
        from_attributes = True


class WidgetConfigUpdateRequest(BaseModel):
    """Request model for updating widget configuration"""

    enabled: Optional[bool] = None
    custom_styles: Optional[Dict[str, Any]] = None
    display_settings: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "display_settings": {"reviews_per_page": 20},
            }
        }
