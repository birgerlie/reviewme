"""
Test Media Model
Following TDD: Write tests first
"""
import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from media_service.domain.models.media import (
    Media,
    MediaType,
    MediaStatus,
    MediaProcessingStatus,
)


@pytest.fixture
def sample_image():
    """Sample image media"""
    return Media(
        id="media_123",
        review_id="review_456",
        merchant_id="merchant_789",
        media_type=MediaType.IMAGE,
        original_filename="product.jpg",
        file_size=1024000,  # 1MB
        mime_type="image/jpeg",
        storage_path="reviews/merchant_789/review_456/media_123.jpg",
        cdn_url="https://cdn.reviewplatform.com/media_123.jpg",
        status=MediaStatus.ACTIVE,
        processing_status=MediaProcessingStatus.COMPLETED,
        width=1920,
        height=1080,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_video():
    """Sample video media"""
    return Media(
        id="media_video_123",
        review_id="review_456",
        merchant_id="merchant_789",
        media_type=MediaType.VIDEO,
        original_filename="demo.mp4",
        file_size=5242880,  # 5MB
        mime_type="video/mp4",
        storage_path="reviews/merchant_789/review_456/media_video_123.mp4",
        cdn_url="https://cdn.reviewplatform.com/media_video_123.mp4",
        status=MediaStatus.ACTIVE,
        processing_status=MediaProcessingStatus.COMPLETED,
        duration_seconds=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestMediaModel:
    """Test Media domain model"""

    def test_create_image_media(self, sample_image: Media) -> None:
        """
        GIVEN media data
        WHEN Media object created
        THEN has correct properties
        """
        assert sample_image.id == "media_123"
        assert sample_image.media_type == MediaType.IMAGE
        assert sample_image.file_size == 1024000
        assert sample_image.is_image()
        assert not sample_image.is_video()

    def test_create_video_media(self, sample_video: Media) -> None:
        """
        GIVEN video data
        WHEN Media object created
        THEN has correct video properties
        """
        assert sample_video.media_type == MediaType.VIDEO
        assert sample_video.duration_seconds == 30
        assert sample_video.is_video()
        assert not sample_video.is_image()

    def test_media_file_size_validation(self) -> None:
        """
        Business Rule: File size limits
        GIVEN large file
        WHEN creating media
        THEN validates file size
        """
        # Images should be under 10MB
        assert Media.is_valid_file_size(5000000, MediaType.IMAGE) is True
        assert Media.is_valid_file_size(15000000, MediaType.IMAGE) is False

        # Videos should be under 50MB
        assert Media.is_valid_file_size(40000000, MediaType.VIDEO) is True
        assert Media.is_valid_file_size(60000000, MediaType.VIDEO) is False

    def test_media_mime_type_validation(self) -> None:
        """
        Business Rule: Only allow specific file types
        GIVEN file mime type
        WHEN validating
        THEN checks allowed types
        """
        # Valid image types
        assert Media.is_valid_mime_type("image/jpeg", MediaType.IMAGE) is True
        assert Media.is_valid_mime_type("image/png", MediaType.IMAGE) is True
        assert Media.is_valid_mime_type("image/webp", MediaType.IMAGE) is True

        # Invalid image types
        assert Media.is_valid_mime_type("image/gif", MediaType.IMAGE) is False
        assert Media.is_valid_mime_type("application/pdf", MediaType.IMAGE) is False

        # Valid video types
        assert Media.is_valid_mime_type("video/mp4", MediaType.VIDEO) is True
        assert Media.is_valid_mime_type("video/webm", MediaType.VIDEO) is True

        # Invalid video types
        assert Media.is_valid_mime_type("video/avi", MediaType.VIDEO) is False

    def test_media_approve_moderation(self, sample_image: Media) -> None:
        """
        GIVEN media pending moderation
        WHEN approved
        THEN status changes to ACTIVE
        """
        media = Media(
            id="media_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.IMAGE,
            original_filename="test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            storage_path="test.jpg",
            cdn_url="https://cdn.test.com/test.jpg",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        media.approve()

        assert media.status == MediaStatus.ACTIVE

    def test_media_reject_moderation(self, sample_image: Media) -> None:
        """
        GIVEN media pending moderation
        WHEN rejected
        THEN status changes to REJECTED
        """
        media = Media(
            id="media_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.IMAGE,
            original_filename="test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            storage_path="test.jpg",
            cdn_url="https://cdn.test.com/test.jpg",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        media.reject("Inappropriate content")

        assert media.status == MediaStatus.REJECTED
        assert media.moderation_reason == "Inappropriate content"

    def test_media_processing_status_flow(self, sample_image: Media) -> None:
        """
        GIVEN media upload
        WHEN processing
        THEN status transitions correctly
        """
        media = Media(
            id="media_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.IMAGE,
            original_filename="test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            storage_path="test.jpg",
            cdn_url="https://cdn.test.com/test.jpg",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert media.processing_status == MediaProcessingStatus.PENDING

        media.mark_processing()
        assert media.processing_status == MediaProcessingStatus.PROCESSING

        media.mark_completed()
        assert media.processing_status == MediaProcessingStatus.COMPLETED

    def test_media_processing_failed(self, sample_image: Media) -> None:
        """
        GIVEN media processing
        WHEN processing fails
        THEN marks as failed with error
        """
        media = Media(
            id="media_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.IMAGE,
            original_filename="test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            storage_path="test.jpg",
            cdn_url="https://cdn.test.com/test.jpg",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        media.mark_failed("Failed to optimize image")

        assert media.processing_status == MediaProcessingStatus.FAILED
        assert media.processing_error == "Failed to optimize image"

    def test_get_thumbnail_url(self, sample_image: Media) -> None:
        """
        GIVEN image media
        WHEN getting thumbnail
        THEN returns CDN thumbnail URL
        """
        thumbnail_url = sample_image.get_thumbnail_url()

        assert "thumbnail" in thumbnail_url
        assert sample_image.id in thumbnail_url

    def test_all_media_types_valid(self) -> None:
        """Verify all media types are defined"""
        assert MediaType.IMAGE == MediaType.IMAGE
        assert MediaType.VIDEO == MediaType.VIDEO

    def test_all_media_statuses_valid(self) -> None:
        """Verify all media statuses are defined"""
        assert MediaStatus.ACTIVE
        assert MediaStatus.PENDING_MODERATION
        assert MediaStatus.REJECTED
        assert MediaStatus.DELETED

    def test_all_processing_statuses_valid(self) -> None:
        """Verify all processing statuses are defined"""
        assert MediaProcessingStatus.PENDING
        assert MediaProcessingStatus.PROCESSING
        assert MediaProcessingStatus.COMPLETED
        assert MediaProcessingStatus.FAILED
