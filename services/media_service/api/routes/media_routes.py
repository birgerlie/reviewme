"""
Media API Routes
FastAPI endpoints for media service
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List

from media_service.api.models import (
    MediaUploadResponse,
    MediaResponse,
    MediaModerateRequest,
    MediaListResponse,
)
from media_service.domain.services.media_service import MediaService
from media_service.domain.models.media import MediaType, MediaStatus

router = APIRouter(tags=["media"])


# Mock dependencies (to be implemented with real services)
async def get_media_service() -> MediaService:
    """Dependency: Get media service"""
    from unittest.mock import Mock, AsyncMock

    mock_repo = Mock()
    mock_repo.create = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_by_review = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.delete = AsyncMock()

    mock_storage = Mock()
    mock_storage.upload_file = AsyncMock()
    mock_storage.delete_file = AsyncMock()

    mock_cdn = Mock()
    mock_cdn.get_url = Mock(return_value="https://cdn.test.com/media.jpg")
    mock_cdn.invalidate_cache = AsyncMock()

    mock_processor = Mock()
    mock_processor.get_dimensions = Mock(return_value=(1920, 1080))
    mock_processor.optimize_image = AsyncMock()
    mock_processor.generate_thumbnail = AsyncMock()

    return MediaService(mock_repo, mock_storage, mock_cdn, mock_processor)


@router.post(
    "/api/v1/media/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload media file",
    description="Upload image or video for a review",
)
async def upload_media(
    review_id: str = Form(...),
    merchant_id: str = Form(...),
    file: UploadFile = File(...),
    service: MediaService = Depends(get_media_service),
) -> MediaUploadResponse:
    """
    Upload media file

    **Supported formats:**
    - Images: JPEG, PNG, WebP (max 10MB)
    - Videos: MP4, WebM (max 50MB)

    **Process:**
    1. Upload to storage
    2. Create media record
    3. Queue for processing
    4. Queue for moderation
    """
    try:
        # Read file data
        file_data = await file.read()
        filename = file.filename or "upload"
        mime_type = file.content_type or "application/octet-stream"

        # Upload media
        media = await service.upload_media(
            review_id=review_id,
            merchant_id=merchant_id,
            file_data=file_data,
            filename=filename,
            mime_type=mime_type,
        )

        return MediaUploadResponse(
            id=media.id,
            review_id=media.review_id,
            media_type=media.media_type.value,
            cdn_url=media.cdn_url,
            status=media.status.value,
            processing_status=media.processing_status.value,
            thumbnail_url=media.get_thumbnail_url() if media.is_image() else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload media: {str(e)}",
        )


@router.get(
    "/api/v1/media/{media_id}",
    response_model=MediaResponse,
    summary="Get media details",
    description="Get details for a specific media file",
)
async def get_media(
    media_id: str,
    service: MediaService = Depends(get_media_service),
) -> MediaResponse:
    """Get media details"""
    try:
        media = await service.media_repository.get_by_id(media_id)

        if media is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found",
            )

        return MediaResponse(
            id=media.id,
            review_id=media.review_id,
            merchant_id=media.merchant_id,
            media_type=media.media_type.value,
            original_filename=media.original_filename,
            file_size=media.file_size,
            mime_type=media.mime_type,
            cdn_url=media.cdn_url,
            status=media.status.value,
            processing_status=media.processing_status.value,
            width=media.width,
            height=media.height,
            duration_seconds=media.duration_seconds,
            thumbnail_url=(
                media.get_thumbnail_url() if media.is_image() else media.thumbnail_url
            ),
            moderation_reason=media.moderation_reason,
            created_at=media.created_at,
            updated_at=media.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media: {str(e)}",
        )


@router.get(
    "/api/v1/media/review/{review_id}",
    response_model=MediaListResponse,
    summary="Get media for review",
    description="Get all media files for a specific review",
)
async def get_review_media(
    review_id: str,
    service: MediaService = Depends(get_media_service),
) -> MediaListResponse:
    """Get all media for a review"""
    try:
        media_list = await service.get_review_media(review_id)

        return MediaListResponse(
            media=[
                MediaResponse(
                    id=m.id,
                    review_id=m.review_id,
                    merchant_id=m.merchant_id,
                    media_type=m.media_type.value,
                    original_filename=m.original_filename,
                    file_size=m.file_size,
                    mime_type=m.mime_type,
                    cdn_url=m.cdn_url,
                    status=m.status.value,
                    processing_status=m.processing_status.value,
                    width=m.width,
                    height=m.height,
                    duration_seconds=m.duration_seconds,
                    thumbnail_url=(
                        m.get_thumbnail_url() if m.is_image() else m.thumbnail_url
                    ),
                    moderation_reason=m.moderation_reason,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in media_list
            ],
            total=len(media_list),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review media: {str(e)}",
        )


@router.post(
    "/api/v1/media/{media_id}/process",
    response_model=MediaResponse,
    summary="Process media",
    description="Process media (optimization, thumbnails, transcoding)",
)
async def process_media(
    media_id: str,
    service: MediaService = Depends(get_media_service),
) -> MediaResponse:
    """Process media"""
    try:
        media = await service.process_media(media_id)

        return MediaResponse(
            id=media.id,
            review_id=media.review_id,
            merchant_id=media.merchant_id,
            media_type=media.media_type.value,
            original_filename=media.original_filename,
            file_size=media.file_size,
            mime_type=media.mime_type,
            cdn_url=media.cdn_url,
            status=media.status.value,
            processing_status=media.processing_status.value,
            width=media.width,
            height=media.height,
            duration_seconds=media.duration_seconds,
            created_at=media.created_at,
            updated_at=media.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process media: {str(e)}",
        )


@router.post(
    "/api/v1/media/{media_id}/moderate",
    response_model=MediaResponse,
    summary="Moderate media",
    description="Approve or reject media after moderation review",
)
async def moderate_media(
    media_id: str,
    request: MediaModerateRequest,
    service: MediaService = Depends(get_media_service),
) -> MediaResponse:
    """Moderate media (approve or reject)"""
    try:
        if request.approved:
            media = await service.approve_media(media_id)
        else:
            reason = request.reason or "Content does not meet guidelines"
            media = await service.reject_media(media_id, reason)

        return MediaResponse(
            id=media.id,
            review_id=media.review_id,
            merchant_id=media.merchant_id,
            media_type=media.media_type.value,
            original_filename=media.original_filename,
            file_size=media.file_size,
            mime_type=media.mime_type,
            cdn_url=media.cdn_url,
            status=media.status.value,
            processing_status=media.processing_status.value,
            width=media.width,
            height=media.height,
            duration_seconds=media.duration_seconds,
            moderation_reason=media.moderation_reason,
            created_at=media.created_at,
            updated_at=media.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to moderate media: {str(e)}",
        )


@router.delete(
    "/api/v1/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete media",
    description="Delete media file and record",
)
async def delete_media(
    media_id: str,
    service: MediaService = Depends(get_media_service),
) -> None:
    """Delete media"""
    try:
        deleted = await service.delete_media(media_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete media: {str(e)}",
        )
