"""
Media domain model
Represents uploaded images and videos for reviews
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class MediaType(Enum):
    """Media types"""

    IMAGE = "image"
    VIDEO = "video"


class MediaStatus(Enum):
    """Media moderation status"""

    PENDING_MODERATION = "pending_moderation"
    ACTIVE = "active"
    REJECTED = "rejected"
    DELETED = "deleted"


class MediaProcessingStatus(Enum):
    """Media processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Media:
    """
    Media domain model

    Represents uploaded images and videos for reviews.
    Supports moderation, processing, and CDN delivery.

    Business Rules:
    - Images: max 10MB, jpeg/png/webp only
    - Videos: max 50MB, mp4/webm only
    - All media requires moderation before going live
    - Automatic thumbnail generation for images
    - Video transcoding for compatibility
    """

    # Required fields
    review_id: str
    merchant_id: str
    media_type: MediaType
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    cdn_url: str
    status: MediaStatus
    processing_status: MediaProcessingStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields
    id: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    moderation_reason: Optional[str] = None
    processing_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Business Rules: File size limits (bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

    # Business Rules: Allowed MIME types
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]

    @staticmethod
    def is_valid_file_size(file_size: int, media_type: MediaType) -> bool:
        """
        Validate file size

        Business Rule:
        - Images: max 10MB
        - Videos: max 50MB
        """
        if media_type == MediaType.IMAGE:
            return file_size <= Media.MAX_IMAGE_SIZE
        elif media_type == MediaType.VIDEO:
            return file_size <= Media.MAX_VIDEO_SIZE
        return False

    @staticmethod
    def is_valid_mime_type(mime_type: str, media_type: MediaType) -> bool:
        """
        Validate MIME type

        Business Rule:
        - Images: jpeg, png, webp only
        - Videos: mp4, webm only
        """
        if media_type == MediaType.IMAGE:
            return mime_type in Media.ALLOWED_IMAGE_TYPES
        elif media_type == MediaType.VIDEO:
            return mime_type in Media.ALLOWED_VIDEO_TYPES
        return False

    def is_image(self) -> bool:
        """Check if media is an image"""
        return self.media_type == MediaType.IMAGE

    def is_video(self) -> bool:
        """Check if media is a video"""
        return self.media_type == MediaType.VIDEO

    def approve(self) -> None:
        """
        Approve media after moderation

        Business Rule: Only PENDING_MODERATION media can be approved
        """
        if self.status == MediaStatus.PENDING_MODERATION:
            self.status = MediaStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def reject(self, reason: str) -> None:
        """
        Reject media after moderation

        Args:
            reason: Reason for rejection
        """
        self.status = MediaStatus.REJECTED
        self.moderation_reason = reason
        self.updated_at = datetime.utcnow()

    def mark_processing(self) -> None:
        """Mark media as processing (optimization, transcoding)"""
        self.processing_status = MediaProcessingStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark media processing as completed"""
        self.processing_status = MediaProcessingStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """
        Mark media processing as failed

        Args:
            error: Error message
        """
        self.processing_status = MediaProcessingStatus.FAILED
        self.processing_error = error
        self.updated_at = datetime.utcnow()

    def get_thumbnail_url(self, size: str = "medium") -> str:
        """
        Get thumbnail URL

        Args:
            size: Thumbnail size (small, medium, large)

        Returns:
            CDN URL for thumbnail
        """
        if self.is_video() and self.thumbnail_url:
            return self.thumbnail_url

        # For images, generate thumbnail URL
        base_url = self.cdn_url.rsplit(".", 1)[0]
        extension = self.cdn_url.rsplit(".", 1)[1]
        return f"{base_url}_thumbnail_{size}.{extension}"

    def __repr__(self) -> str:
        return (
            f"Media(id={self.id}, type={self.media_type.value}, "
            f"status={self.status.value}, processing={self.processing_status.value})"
        )
