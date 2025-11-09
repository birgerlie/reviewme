"""
Media Service
Business logic for media upload, processing, and CDN delivery
"""
from typing import List, Optional
from datetime import datetime
import uuid

from media_service.domain.models.media import (
    Media,
    MediaType,
    MediaStatus,
    MediaProcessingStatus,
)


class MediaService:
    """
    Media Service

    Handles media upload, processing, moderation, and CDN delivery.

    Business Rules:
    - Validate file size and MIME type before upload
    - All media starts as PENDING_MODERATION
    - Process images: optimize, generate thumbnails
    - Process videos: transcode, generate thumbnails
    - CDN delivery for public access
    """

    def __init__(
        self,
        media_repository,
        storage_service,
        cdn_service,
        image_processor,
    ):
        """
        Initialize Media Service

        Args:
            media_repository: Repository for media persistence
            storage_service: Service for file storage (S3)
            cdn_service: Service for CDN delivery
            image_processor: Service for image optimization
        """
        self.media_repository = media_repository
        self.storage_service = storage_service
        self.cdn_service = cdn_service
        self.image_processor = image_processor

    async def upload_media(
        self,
        review_id: str,
        merchant_id: str,
        file_data: bytes,
        filename: str,
        mime_type: str,
    ) -> Media:
        """
        Upload media file

        Args:
            review_id: Review ID
            merchant_id: Merchant ID
            file_data: Binary file data
            filename: Original filename
            mime_type: MIME type

        Returns:
            Created Media object

        Raises:
            ValueError: If file invalid
        """
        # Determine media type
        if mime_type.startswith("image/"):
            media_type = MediaType.IMAGE
        elif mime_type.startswith("video/"):
            media_type = MediaType.VIDEO
        else:
            raise ValueError(f"Invalid MIME type: {mime_type}")

        # Business Rule: Validate file size
        file_size = len(file_data)
        if not Media.is_valid_file_size(file_size, media_type):
            max_size = (
                Media.MAX_IMAGE_SIZE
                if media_type == MediaType.IMAGE
                else Media.MAX_VIDEO_SIZE
            )
            raise ValueError(
                f"File size {file_size} exceeds maximum {max_size} for {media_type.value}"
            )

        # Business Rule: Validate MIME type
        if not Media.is_valid_mime_type(mime_type, media_type):
            allowed = (
                Media.ALLOWED_IMAGE_TYPES
                if media_type == MediaType.IMAGE
                else Media.ALLOWED_VIDEO_TYPES
            )
            raise ValueError(f"MIME type {mime_type} not in allowed types: {allowed}")

        # Generate unique media ID
        media_id = f"media_{uuid.uuid4().hex[:16]}"

        # Upload to storage
        storage_path = await self.storage_service.upload_file(
            file_data=file_data,
            path=f"reviews/{merchant_id}/{review_id}/{media_id}",
            content_type=mime_type,
        )

        # Get CDN URL
        cdn_url = self.cdn_service.get_url(storage_path)

        # Get dimensions for images
        width = None
        height = None
        if media_type == MediaType.IMAGE:
            width, height = self.image_processor.get_dimensions(file_data)

        # Create media record
        media = Media(
            id=media_id,
            review_id=review_id,
            merchant_id=merchant_id,
            media_type=media_type,
            original_filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            cdn_url=cdn_url,
            status=MediaStatus.PENDING_MODERATION,  # Business Rule
            processing_status=MediaProcessingStatus.PENDING,
            width=width,
            height=height,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Save to repository
        created_media = await self.media_repository.create(media)

        return created_media

    async def process_media(self, media_id: str) -> Media:
        """
        Process media (optimization, transcoding, thumbnails)

        Args:
            media_id: Media ID

        Returns:
            Updated Media object
        """
        media = await self.media_repository.get_by_id(media_id)

        if media is None:
            raise ValueError(f"Media {media_id} not found")

        # Mark as processing
        media.mark_processing()
        await self.media_repository.update(media)

        try:
            if media.is_image():
                # Optimize image
                optimized_data = await self.image_processor.optimize_image(
                    media.storage_path
                )

                # Generate thumbnail
                thumbnail_data = await self.image_processor.generate_thumbnail(
                    media.storage_path, size="medium"
                )

            # elif media.is_video():
            #     # Transcode video (would use FFmpeg or cloud service)
            #     # Generate video thumbnail
            #     pass

            # Mark as completed
            media.mark_completed()

        except Exception as e:
            # Mark as failed
            media.mark_failed(str(e))

        # Update repository
        updated_media = await self.media_repository.update(media)

        return updated_media

    async def approve_media(self, media_id: str) -> Media:
        """
        Approve media after moderation

        Args:
            media_id: Media ID

        Returns:
            Updated Media object
        """
        media = await self.media_repository.get_by_id(media_id)

        if media is None:
            raise ValueError(f"Media {media_id} not found")

        media.approve()

        updated_media = await self.media_repository.update(media)

        return updated_media

    async def reject_media(self, media_id: str, reason: str) -> Media:
        """
        Reject media after moderation

        Args:
            media_id: Media ID
            reason: Rejection reason

        Returns:
            Updated Media object
        """
        media = await self.media_repository.get_by_id(media_id)

        if media is None:
            raise ValueError(f"Media {media_id} not found")

        media.reject(reason)

        updated_media = await self.media_repository.update(media)

        return updated_media

    async def delete_media(self, media_id: str) -> bool:
        """
        Delete media

        Args:
            media_id: Media ID

        Returns:
            True if deleted
        """
        media = await self.media_repository.get_by_id(media_id)

        if media is None:
            return False

        # Delete from storage
        await self.storage_service.delete_file(media.storage_path)

        # Invalidate CDN cache
        await self.cdn_service.invalidate_cache(media.cdn_url)

        # Delete from repository
        deleted = await self.media_repository.delete(media_id)

        return deleted

    async def get_review_media(self, review_id: str) -> List[Media]:
        """
        Get all media for a review

        Args:
            review_id: Review ID

        Returns:
            List of Media objects
        """
        media_list = await self.media_repository.get_by_review(review_id)

        return media_list

    async def get_cdn_url(self, media_id: str) -> str:
        """
        Get CDN URL for media

        Args:
            media_id: Media ID

        Returns:
            CDN URL
        """
        media = await self.media_repository.get_by_id(media_id)

        if media is None:
            raise ValueError(f"Media {media_id} not found")

        return self.cdn_service.get_url(media.storage_path)
