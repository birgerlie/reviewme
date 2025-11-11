"""
Public Review Routes
Endpoints for customer review submission (no authentication required)
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

from platform_service.domain.services.platform_service import PlatformService
from review_service.domain.services.review_service import ReviewService
from review_service.domain.models.review import Review, ReviewRating, ReviewStatus
from review_service.api.dependencies import get_platform_service, get_review_service

router = APIRouter(prefix="/public", tags=["public"])


class ReviewSubmissionRequest(BaseModel):
    """
    Public review submission request

    Submitted by customers via email link with review token
    """

    token: str = Field(..., description="Review token from email")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: str = Field(..., min_length=1, max_length=500, description="Review title")
    content: str = Field(
        ..., min_length=1, max_length=5000, description="Review content"
    )
    media_urls: List[str] = Field(
        default_factory=list, max_items=10, description="Uploaded media URLs"
    )


class TokenValidationResponse(BaseModel):
    """Response for token validation"""

    valid: bool
    expired: bool
    used: bool
    product_info: Optional[dict] = None
    error: Optional[str] = None


@router.get("/review/validate/{token}")
async def validate_token(
    token: str,
    platform_service: PlatformService = Depends(get_platform_service),
):
    """
    Validate review token

    Called when customer opens email link to check if token is valid.
    Frontend uses this to show form or error message.

    Args:
        token: Review token string

    Returns:
        Token validation status and product info

    Example:
        GET /public/review/validate/rt_abc123...
        → Returns: {"valid": true, "product_info": {...}}
    """
    try:
        # Validate token using PlatformService
        token_entity = await platform_service.validate_review_token(token)

        if not token_entity:
            return TokenValidationResponse(
                valid=False,
                expired=False,
                used=False,
                error="Token not found"
            )

        if token_entity.is_expired():
            return TokenValidationResponse(
                valid=False,
                expired=True,
                used=token_entity.used,
                error="Token has expired"
            )

        if token_entity.used:
            return TokenValidationResponse(
                valid=False,
                expired=False,
                used=True,
                error="Token has already been used"
            )

        # Get product info
        product = await platform_service.get_product_details(
            token_entity.merchant_id,
            token_entity.product_id
        )

        return TokenValidationResponse(
            valid=True,
            expired=False,
            used=False,
            product_info={
                "product_id": product.platform_product_id,
                "title": product.title,
                "image_url": product.image_url,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token validation failed: {str(e)}",
        )


@router.post("/review/submit", status_code=status.HTTP_201_CREATED)
async def submit_review(
    request: ReviewSubmissionRequest,
    platform_service: PlatformService = Depends(get_platform_service),
    review_service: ReviewService = Depends(get_review_service),
):
    """
    Submit review with token

    Public endpoint for customers to submit reviews.
    Token ensures only customers who purchased can review.

    Security:
    - Token is validated (not expired, not used)
    - Token is marked as used atomically (prevents duplicate submissions)
    - Review is tied to verified purchase

    Flow:
    1. Validate token
    2. Get product info from token
    3. Create review with verified_purchase=True
    4. Mark token as used (atomic!)
    5. Send confirmation email
    6. Return success

    Args:
        request: Review submission data

    Returns:
        Created review

    Example:
        POST /public/review/submit
        {
            "token": "rt_abc123...",
            "rating": 5,
            "title": "Great product!",
            "content": "I love this product...",
            "media_urls": ["https://r2.example.com/image1.jpg"]
        }
        → Returns: {"id": "rev_123", "status": "pending", ...}
    """
    try:
        # Step 1: Validate token
        token_entity = await platform_service.validate_review_token(request.token)

        if not token_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid token"
            )

        if not token_entity.is_valid():
            if token_entity.is_expired():
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Token has expired"
                )
            elif token_entity.used:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Token has already been used"
                )

        # Step 2: Create review
        review = Review(
            id=None,
            merchant_id=token_entity.merchant_id,
            product_id=token_entity.product_id,
            customer_id=token_entity.customer_email,  # Use email as customer ID
            rating=ReviewRating(request.rating),
            title=request.title,
            content=request.content,
            status=ReviewStatus.PENDING,  # Pending until moderated
            verified_purchase=True,  # Came from order token
            media_urls=request.media_urls,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            attributes={
                "order_id": token_entity.order_id,
                "token_id": token_entity.id,
            }
        )

        # Step 3: Save review
        created_review = await review_service.create_review(review)

        # Step 4: Mark token as used (atomic!)
        success = await platform_service.mark_token_used(request.token)
        if not success:
            # Race condition - token was used by another request
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Token has already been used"
            )

        # Step 5: Event published by review_service.create_review()
        # No need to publish event here - the service handles it

        return {
            "id": created_review.id,
            "status": created_review.status.value,
            "message": "Review submitted successfully. It will be visible after moderation.",
            "verified_purchase": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review submission failed: {str(e)}",
        )


@router.get("/review/{token}")
async def get_review_form_data(
    token: str,
    platform_service: PlatformService = Depends(get_platform_service),
):
    """
    Get data for review form

    Returns product info and customer info pre-filled from token.
    Frontend uses this to render the review form.

    Args:
        token: Review token

    Returns:
        Form data (product info, customer info, token validity)

    Example:
        GET /public/review/rt_abc123...
        → Returns: {
            "valid": true,
            "product": {...},
            "customer_name": "John Doe",
            "customer_email": "john@example.com"
        }
    """
    try:
        # Validate token
        token_entity = await platform_service.validate_review_token(token)

        if not token_entity or not token_entity.is_valid():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid, expired, or used token"
            )

        # Get product info
        product = await platform_service.get_product_details(
            token_entity.merchant_id,
            token_entity.product_id
        )

        return {
            "valid": True,
            "product": {
                "title": product.title,
                "image_url": product.image_url,
            },
            "customer_name": token_entity.customer_name,
            "customer_email": token_entity.customer_email,
            "expires_at": token_entity.expires_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get form data: {str(e)}",
        )
