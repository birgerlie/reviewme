"""
Test Media Service
Following TDD: Write tests first
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from media_service.domain.services.media_service import MediaService
from media_service.domain.models.media import (
    Media,
    MediaType,
    MediaStatus,
    MediaProcessingStatus,
)


@pytest.fixture
def mock_media_repo():
    """Mock media repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_review = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_storage_service():
    """Mock storage service (S3)"""
    storage = Mock()
    storage.upload_file = AsyncMock()
    storage.delete_file = AsyncMock()
    storage.get_url = AsyncMock()
    return storage


@pytest.fixture
def mock_cdn_service():
    """Mock CDN service"""
    cdn = Mock()
    cdn.get_url = Mock()
    cdn.invalidate_cache = AsyncMock()
    return cdn


@pytest.fixture
def mock_image_processor():
    """Mock image processor"""
    processor = Mock()
    processor.optimize_image = AsyncMock()
    processor.generate_thumbnail = AsyncMock()
    processor.get_dimensions = Mock()
    return processor


@pytest.fixture
def media_service(
    mock_media_repo, mock_storage_service, mock_cdn_service, mock_image_processor
):
    """Create MediaService with mocked dependencies"""
    return MediaService(
        media_repository=mock_media_repo,
        storage_service=mock_storage_service,
        cdn_service=mock_cdn_service,
        image_processor=mock_image_processor,
    )


@pytest.mark.asyncio
class TestMediaService:
    """Test Media Service business logic"""

    async def test_upload_image(
        self,
        media_service,
        mock_media_repo,
        mock_storage_service,
        mock_image_processor,
    ) -> None:
        """
        GIVEN image file
        WHEN upload_media called
        THEN uploads to storage and creates media record
        """
        file_data = b"fake image data"
        filename = "product.jpg"

        mock_image_processor.get_dimensions.return_value = (1920, 1080)
        mock_storage_service.upload_file.return_value = "reviews/test/image.jpg"
        mock_media_repo.create.return_value = Media(
            id="media_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.IMAGE,
            original_filename=filename,
            file_size=len(file_data),
            mime_type="image/jpeg",
            storage_path="reviews/test/image.jpg",
            cdn_url="https://cdn.test.com/image.jpg",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.PENDING,
            width=1920,
            height=1080,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await media_service.upload_media(
            review_id="review_456",
            merchant_id="merchant_789",
            file_data=file_data,
            filename=filename,
            mime_type="image/jpeg",
        )

        assert result.id == "media_123"
        assert result.media_type == MediaType.IMAGE
        assert result.status == MediaStatus.PENDING_MODERATION
        mock_storage_service.upload_file.assert_called_once()
        mock_media_repo.create.assert_called_once()

    async def test_upload_video(
        self,
        media_service,
        mock_media_repo,
        mock_storage_service,
    ) -> None:
        """
        GIVEN video file
        WHEN upload_media called
        THEN uploads to storage
        """
        file_data = b"fake video data"
        filename = "demo.mp4"

        mock_storage_service.upload_file.return_value = "reviews/test/video.mp4"
        mock_media_repo.create.return_value = Media(
            id="media_video_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.VIDEO,
            original_filename=filename,
            file_size=len(file_data),
            mime_type="video/mp4",
            storage_path="reviews/test/video.mp4",
            cdn_url="https://cdn.test.com/video.mp4",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await media_service.upload_media(
            review_id="review_456",
            merchant_id="merchant_789",
            file_data=file_data,
            filename=filename,
            mime_type="video/mp4",
        )

        assert result.media_type == MediaType.VIDEO
        assert result.processing_status == MediaProcessingStatus.PENDING

    async def test_upload_invalid_file_size(self, media_service) -> None:
        """
        Business Rule: File size limits
        GIVEN file too large
        WHEN upload_media called
        THEN raises ValueError
        """
        # 15MB file (over 10MB limit for images)
        file_data = b"x" * (15 * 1024 * 1024)

        with pytest.raises(ValueError, match="File size"):
            await media_service.upload_media(
                review_id="review_456",
                merchant_id="merchant_789",
                file_data=file_data,
                filename="large.jpg",
                mime_type="image/jpeg",
            )

    async def test_upload_invalid_mime_type(self, media_service) -> None:
        """
        Business Rule: Only specific file types allowed
        GIVEN invalid file type
        WHEN upload_media called
        THEN raises ValueError
        """
        file_data = b"fake data"

        with pytest.raises(ValueError, match="MIME type"):
            await media_service.upload_media(
                review_id="review_456",
                merchant_id="merchant_789",
                file_data=file_data,
                filename="file.pdf",
                mime_type="application/pdf",
            )

    async def test_process_image(
        self,
        media_service,
        mock_media_repo,
        mock_image_processor,
    ) -> None:
        """
        GIVEN uploaded image
        WHEN process_media called
        THEN optimizes and generates thumbnails
        """
        media = Media(
            id="media_123",
            review_id="review_456",
            merchant_id="merchant_789",
            media_type=MediaType.IMAGE,
            original_filename="test.jpg",
            file_size=1000000,
            mime_type="image/jpeg",
            storage_path="test.jpg",
            cdn_url="https://cdn.test.com/test.jpg",
            status=MediaStatus.PENDING_MODERATION,
            processing_status=MediaProcessingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_media_repo.get_by_id.return_value = media
        mock_image_processor.optimize_image.return_value = b"optimized image"
        mock_image_processor.generate_thumbnail.return_value = b"thumbnail"
        mock_media_repo.update.return_value = media

        result = await media_service.process_media("media_123")

        assert result.processing_status == MediaProcessingStatus.COMPLETED
        mock_image_processor.optimize_image.assert_called_once()
        mock_image_processor.generate_thumbnail.assert_called_once()

    async def test_approve_media(
        self,
        media_service,
        mock_media_repo,
    ) -> None:
        """
        GIVEN media pending moderation
        WHEN approve_media called
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

        mock_media_repo.get_by_id.return_value = media
        mock_media_repo.update.return_value = media

        result = await media_service.approve_media("media_123")

        assert result.status == MediaStatus.ACTIVE
        mock_media_repo.update.assert_called_once()

    async def test_reject_media(
        self,
        media_service,
        mock_media_repo,
        mock_cdn_service,
    ) -> None:
        """
        GIVEN media pending moderation
        WHEN reject_media called
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

        mock_media_repo.get_by_id.return_value = media
        mock_media_repo.update.return_value = media

        result = await media_service.reject_media("media_123", "Inappropriate content")

        assert result.status == MediaStatus.REJECTED
        assert result.moderation_reason == "Inappropriate content"

    async def test_delete_media(
        self,
        media_service,
        mock_media_repo,
        mock_storage_service,
        mock_cdn_service,
    ) -> None:
        """
        GIVEN media
        WHEN delete_media called
        THEN removes from storage and marks deleted
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
            status=MediaStatus.ACTIVE,
            processing_status=MediaProcessingStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_media_repo.get_by_id.return_value = media
        mock_storage_service.delete_file.return_value = True
        mock_media_repo.delete.return_value = True

        result = await media_service.delete_media("media_123")

        assert result is True
        mock_storage_service.delete_file.assert_called_once()
        mock_cdn_service.invalidate_cache.assert_called_once()
        mock_media_repo.delete.assert_called_once()

    async def test_get_review_media(
        self,
        media_service,
        mock_media_repo,
    ) -> None:
        """
        GIVEN review with media
        WHEN get_review_media called
        THEN returns all media for review
        """
        media_list = [
            Media(
                id=f"media_{i}",
                review_id="review_456",
                merchant_id="merchant_789",
                media_type=MediaType.IMAGE,
                original_filename=f"test{i}.jpg",
                file_size=1000,
                mime_type="image/jpeg",
                storage_path=f"test{i}.jpg",
                cdn_url=f"https://cdn.test.com/test{i}.jpg",
                status=MediaStatus.ACTIVE,
                processing_status=MediaProcessingStatus.COMPLETED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(3)
        ]

        mock_media_repo.get_by_review.return_value = media_list

        result = await media_service.get_review_media("review_456")

        assert len(result) == 3
        assert all(m.review_id == "review_456" for m in result)

    async def test_get_cdn_url(
        self,
        media_service,
        mock_media_repo,
        mock_cdn_service,
    ) -> None:
        """
        GIVEN media
        WHEN get_cdn_url called
        THEN returns CDN URL
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
            status=MediaStatus.ACTIVE,
            processing_status=MediaProcessingStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_media_repo.get_by_id.return_value = media
        mock_cdn_service.get_url.return_value = "https://cdn.test.com/test.jpg"

        result = await media_service.get_cdn_url("media_123")

        assert "cdn.test.com" in result
