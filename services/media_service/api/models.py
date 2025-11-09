"""
API Models for Media Service
Pydantic schemas for request/response
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class MediaUploadResponse(BaseModel):
    """Response model for media upload"""

    id: str
    review_id: str
    media_type: str
    cdn_url: str
    status: str
    processing_status: str
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "media_123",
                "review_id": "review_456",
                "media_type": "image",
                "cdn_url": "https://cdn.reviewplatform.com/media_123.jpg",
                "status": "pending_moderation",
                "processing_status": "pending",
            }
        }


class MediaResponse(BaseModel):
    """Response model for media details"""

    id: str
    review_id: str
    merchant_id: str
    media_type: str
    original_filename: str
    file_size: int
    mime_type: str
    cdn_url: str
    status: str
    processing_status: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    moderation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaModerateRequest(BaseModel):
    """Request model for media moderation"""

    approved: bool
    reason: Optional[str] = Field(None, description="Rejection reason if not approved")

    class Config:
        json_schema_extra = {
            "example": {
                "approved": False,
                "reason": "Inappropriate content",
            }
        }


class MediaListResponse(BaseModel):
    """Response model for media list"""

    media: list[MediaResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "media": [],
                "total": 0,
            }
        }
