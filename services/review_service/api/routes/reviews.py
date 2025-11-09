"""
Review API Routes
FastAPI endpoints for review operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from datetime import datetime

from review_service.api.models import (
    ReviewCreateRequest,
    ReviewResponse,
    ReviewListResponse,
    RatingResponse,
    RatingStatsResponse,
    SuccessResponse,
)
from review_service.api.dependencies import get_review_service, verify_api_key
from review_service.domain.services.review_service import ReviewService
from review_service.domain.models.review import Review, ReviewRating, ReviewStatus
from shared.config.settings import get_settings

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])
settings = get_settings()


@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new review",
    description="Create a new product review. Verified purchases with 4+ stars are auto-approved.",
)
async def create_review(
    request: ReviewCreateRequest,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> ReviewResponse:
    """Create a new review"""
    # Convert request to domain model
    review = Review(
        id=None,
        product_id=request.product_id,
        customer_id=request.customer_id,
        rating=ReviewRating(request.rating),
        title=request.title,
        content=request.content,
        status=ReviewStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        verified_purchase=request.verified_purchase,
        media_urls=request.media_urls,
        attributes=request.attributes,
    )

    # Create review
    created_review = await service.create_review(review)

    # Convert to response
    return _review_to_response(created_review)


@router.get(
    "/products/{product_id}",
    response_model=ReviewListResponse,
    summary="Get reviews for a product",
    description="Get all approved reviews for a product with pagination",
)
async def get_product_reviews(
    product_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str = Query(default="approved"),
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> ReviewListResponse:
    """Get reviews for a product"""
    # Parse status
    review_status = ReviewStatus(status) if status else None

    # Get reviews
    reviews = await service.get_product_reviews(
        product_id=product_id, status=review_status, limit=limit, offset=offset
    )

    # Get total count
    from review_service.api.dependencies import get_review_repository

    repo = await get_review_repository.__wrapped__(next(get_review_repository.__defaults__))
    total = await repo.count_by_product(product_id, review_status)

    # Convert to response
    return ReviewListResponse(
        reviews=[_review_to_response(r) for r in reviews],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(reviews)) < total,
    )


@router.get(
    "/products/{product_id}/rating",
    response_model=RatingResponse,
    summary="Get product rating",
    description="Get average rating and review count for a product",
)
async def get_product_rating(
    product_id: str,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> RatingResponse:
    """Get product rating"""
    # Get rating stats
    stats = await service.get_rating_stats(product_id)

    return RatingResponse(
        product_id=product_id,
        average_rating=stats["average_rating"],
        total_reviews=stats["total_reviews"],
    )


@router.get(
    "/products/{product_id}/stats",
    response_model=RatingStatsResponse,
    summary="Get detailed rating statistics",
    description="Get detailed rating statistics including distribution",
)
async def get_rating_stats(
    product_id: str,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> RatingStatsResponse:
    """Get rating statistics"""
    stats = await service.get_rating_stats(product_id)

    return RatingStatsResponse(
        product_id=product_id,
        average_rating=stats["average_rating"],
        total_reviews=stats["total_reviews"],
        rating_distribution=stats["rating_distribution"],
    )


@router.post(
    "/{review_id}/helpful",
    response_model=SuccessResponse,
    summary="Mark review as helpful",
    description="Increment the helpful count for a review",
)
async def mark_review_helpful(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> SuccessResponse:
    """Mark review as helpful"""
    try:
        await service.mark_helpful(review_id)
        return SuccessResponse(success=True, message="Review marked as helpful")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{review_id}/approve",
    response_model=ReviewResponse,
    summary="Approve a review",
    description="Approve a pending review (admin only)",
)
async def approve_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> ReviewResponse:
    """Approve a review"""
    try:
        review = await service.approve_review(review_id)
        return _review_to_response(review)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{review_id}/reject",
    response_model=ReviewResponse,
    summary="Reject a review",
    description="Reject a review (admin only)",
)
async def reject_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> ReviewResponse:
    """Reject a review"""
    try:
        review = await service.reject_review(review_id)
        return _review_to_response(review)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{review_id}/flag",
    response_model=ReviewResponse,
    summary="Flag a review",
    description="Flag a review for moderation",
)
async def flag_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
    api_key: str = Depends(verify_api_key),
) -> ReviewResponse:
    """Flag a review"""
    try:
        review = await service.flag_review(review_id)
        return _review_to_response(review)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


def _review_to_response(review: Review) -> ReviewResponse:
    """Convert domain model to API response"""
    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        customer_id=review.customer_id,
        rating=review.rating.value,
        title=review.title,
        content=review.content,
        status=review.status.value,
        created_at=review.created_at,
        updated_at=review.updated_at,
        verified_purchase=review.verified_purchase,
        helpful_count=review.helpful_count,
        media_urls=review.media_urls,
        attributes=review.attributes,
    )
