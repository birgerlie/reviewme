"""
API Models for AI Service
Pydantic schemas for request/response
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List


class StyleGenerationRequest(BaseModel):
    """Request model for style generation"""

    brand_website_url: HttpUrl
    brand_colors: Optional[Dict[str, str]] = Field(
        default=None, description="Brand color palette (hex values)"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="User preferences (layout, theme, etc.)"
    )
    include_responsive: bool = Field(
        default=False, description="Include responsive breakpoints"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brand_website_url": "https://example.com",
                "brand_colors": {"primary": "#FF0000", "secondary": "#00FF00"},
                "preferences": {"layout": "grid", "theme": "modern"},
                "include_responsive": True,
            }
        }


class StyleGenerationResponse(BaseModel):
    """Response model for style generation"""

    style_config: Dict[str, Any] = Field(..., description="Generated style configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "style_config": {
                    "colors": {
                        "primary": "#FF0000",
                        "secondary": "#00FF00",
                        "text": "#333333",
                    },
                    "typography": {"fontFamily": "Arial, sans-serif", "fontSize": "16px"},
                    "spacing": {"md": "16px", "lg": "24px"},
                }
            }
        }


class CSSGenerationRequest(BaseModel):
    """Request model for CSS generation"""

    style_config: Dict[str, Any] = Field(..., description="Style configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "style_config": {
                    "colors": {"primary": "#FF0000"},
                    "typography": {"fontFamily": "Arial"},
                }
            }
        }


class CSSGenerationResponse(BaseModel):
    """Response model for CSS generation"""

    css: str = Field(..., description="Generated CSS code")

    class Config:
        json_schema_extra = {
            "example": {
                "css": ".review-widget { color: #FF0000; font-family: Arial; }"
            }
        }


class ReviewSummaryRequest(BaseModel):
    """Request model for review summarization"""

    reviews: List[Dict[str, Any]] = Field(..., description="List of reviews to summarize")
    max_reviews: Optional[int] = Field(
        default=None, description="Maximum reviews to process"
    )
    verified_only: bool = Field(
        default=False, description="Only include verified purchases"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reviews": [
                    {
                        "rating": 5,
                        "title": "Great!",
                        "content": "Excellent product",
                        "verified_purchase": True,
                    }
                ],
                "verified_only": False,
            }
        }


class ReviewSummaryResponse(BaseModel):
    """Response model for review summary"""

    summary: str = Field(..., description="Review summary")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Customers love the quality. Most mention excellent value and fast shipping."
            }
        }


class ProsConsRequest(BaseModel):
    """Request model for pros/cons extraction"""

    reviews: List[Dict[str, Any]]
    max_reviews: Optional[int] = None
    verified_only: bool = False


class ProsConsResponse(BaseModel):
    """Response model for pros/cons"""

    pros: List[str] = Field(..., description="Positive points")
    cons: List[str] = Field(..., description="Negative points")

    class Config:
        json_schema_extra = {
            "example": {
                "pros": ["Excellent quality", "Fast delivery", "Great value"],
                "cons": ["Sizing runs small"],
            }
        }


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis"""

    reviews: List[Dict[str, Any]]


class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis"""

    overall_sentiment: str = Field(..., description="Overall sentiment")
    sentiment_score: float = Field(..., ge=0, le=1, description="Sentiment score 0-1")
    positive_percentage: int = Field(..., ge=0, le=100)
    negative_percentage: int = Field(..., ge=0, le=100)
    neutral_percentage: int = Field(..., ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "overall_sentiment": "positive",
                "sentiment_score": 0.82,
                "positive_percentage": 75,
                "negative_percentage": 10,
                "neutral_percentage": 15,
            }
        }


class KeyThemesRequest(BaseModel):
    """Request model for key themes extraction"""

    reviews: List[Dict[str, Any]]
    max_themes: int = Field(default=5, ge=1, le=10)


class KeyThemesResponse(BaseModel):
    """Response model for key themes"""

    themes: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "themes": [
                    {"theme": "Quality", "mentions": 15, "sentiment": "positive"},
                    {"theme": "Shipping", "mentions": 8, "sentiment": "positive"},
                ]
            }
        }


class HighlightsRequest(BaseModel):
    """Request model for highlights generation"""

    reviews: List[Dict[str, Any]]
    max_highlights: int = Field(default=3, ge=1, le=10)


class HighlightsResponse(BaseModel):
    """Response model for highlights"""

    highlights: List[str]

    class Config:
        json_schema_extra = {
            "example": {"highlights": ["Outstanding quality", "Excellent value"]}
        }
