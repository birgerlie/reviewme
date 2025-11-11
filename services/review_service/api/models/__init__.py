"""
API Models (Pydantic schemas)
Request and Response models for the API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReviewRatingEnum(int, Enum):
    """Review rating enum for API"""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class ReviewStatusEnum(str, Enum):
    """Review status enum for API"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ReviewCreateRequest(BaseModel):
    """Request model for creating a review"""

    product_id: str = Field(..., min_length=1, max_length=255)
    customer_id: str = Field(..., min_length=1, max_length=255)
    rating: ReviewRatingEnum = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=5000)
    verified_purchase: bool = False
    media_urls: List[str] = Field(default_factory=list, max_length=10)
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @validator("media_urls")
    def validate_media_urls(cls, v: List[str]) -> List[str]:
        """Validate media URLs"""
        if len(v) > 10:
            raise ValueError("Maximum 10 media files allowed")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_123",
                "customer_id": "cust_456",
                "rating": 5,
                "title": "Excellent product!",
                "content": "This product exceeded my expectations. Highly recommend!",
                "verified_purchase": True,
                "media_urls": ["https://example.com/photo1.jpg"],
                "attributes": {"size": "Large", "color": "Blue"},
            }
        }


class ReviewResponse(BaseModel):
    """Response model for a review"""

    id: str
    product_id: str
    customer_id: str
    rating: int
    title: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime
    verified_purchase: bool
    helpful_count: int
    media_urls: List[str]
    attributes: Dict[str, Any]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "rev_abc123",
                "product_id": "prod_123",
                "customer_id": "cust_456",
                "rating": 5,
                "title": "Excellent product!",
                "content": "This product exceeded my expectations.",
                "status": "approved",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z",
                "verified_purchase": True,
                "helpful_count": 10,
                "media_urls": ["https://example.com/photo1.jpg"],
                "attributes": {"size": "Large"},
            }
        }


class ReviewUpdateRequest(BaseModel):
    """Request model for updating a review"""

    rating: Optional[ReviewRatingEnum] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    media_urls: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class RatingResponse(BaseModel):
    """Response model for product rating"""

    product_id: str
    average_rating: float
    total_reviews: int

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_123",
                "average_rating": 4.5,
                "total_reviews": 100,
            }
        }


class RatingStatsResponse(BaseModel):
    """Response model for detailed rating statistics"""

    product_id: str
    average_rating: float
    total_reviews: int
    rating_distribution: Dict[int, int]

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_123",
                "average_rating": 4.5,
                "total_reviews": 100,
                "rating_distribution": {5: 60, 4: 25, 3: 10, 2: 3, 1: 2},
            }
        }


class ReviewListResponse(BaseModel):
    """Response model for paginated review list"""

    reviews: List[ReviewResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "reviews": [
                    {
                        "id": "rev_abc123",
                        "product_id": "prod_123",
                        "rating": 5,
                        "title": "Great!",
                        "content": "Love it",
                        "status": "approved",
                        "verified_purchase": True,
                        "helpful_count": 10,
                    }
                ],
                "total": 100,
                "limit": 10,
                "offset": 0,
                "has_more": True,
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    detail: Optional[str] = None

    class Config:
        json_schema_extra = {"example": {"error": "Not Found", "detail": "Review not found"}}


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool
    message: str

    class Config:
        json_schema_extra = {"example": {"success": True, "message": "Operation completed"}}
