"""
Review Service - Business Logic Layer
Contains all business rules for review management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from review_service.domain.models.review import Review, ReviewStatus
from review_service.domain.interfaces.review_repository_interface import (
    IReviewRepository,
)
from review_service.domain.interfaces.cache_interface import ICacheService
from review_service.domain.interfaces.event_bus_interface import IEventBus


class ReviewService:
    """
    Review Service

    Business Logic:
    - Auto-approve verified purchases with 4+ stars
    - Invalidate cache on create/update
    - Publish events for other services
    - Use caching for read operations

    This service is the entry point for all review-related operations
    and contains the core business rules.
    """

    def __init__(
        self,
        review_repository: IReviewRepository,
        cache_service: ICacheService,
        event_bus: IEventBus,
    ) -> None:
        """
        Initialize service with dependencies

        Args:
            review_repository: Repository for data access
            cache_service: Cache for performance
            event_bus: Event bus for publishing events
        """
        self.review_repository = review_repository
        self.cache_service = cache_service
        self.event_bus = event_bus

        # Cache TTL in seconds
        self.CACHE_TTL_REVIEWS = 300  # 5 minutes
        self.CACHE_TTL_RATINGS = 600  # 10 minutes

    async def create_review(self, review: Review) -> Review:
        """
        Create a new review

        Business Rules:
        - Auto-approve verified purchases with rating >= 4
        - Publish review.created event
        - Invalidate product cache

        Args:
            review: Review to create

        Returns:
            Created review
        """
        # Business Rule: Auto-approve verified purchases with high ratings
        if review.verified_purchase and review.is_high_rating():
            review.approve()

        # Create in database
        created_review = await self.review_repository.create(review)

        # Invalidate cache for this product
        await self._invalidate_product_cache(created_review.product_id)

        # Publish event
        await self.event_bus.publish(
            "review.created",
            {
                "review_id": created_review.id,
                "product_id": created_review.product_id,
                "customer_id": created_review.customer_id,
                "rating": created_review.rating.value,
                "status": created_review.status.value,
                "created_at": created_review.created_at.isoformat(),
            },
        )

        return created_review

    async def get_product_reviews(
        self,
        product_id: str,
        status: Optional[ReviewStatus] = ReviewStatus.APPROVED,
        limit: int = 10,
        offset: int = 0,
        use_cache: bool = True,
    ) -> List[Review]:
        """
        Get reviews for a product

        Args:
            product_id: Product identifier
            status: Filter by status (default: APPROVED only)
            limit: Maximum reviews to return
            offset: Pagination offset
            use_cache: Whether to use cache

        Returns:
            List of reviews
        """
        cache_key = f"product:reviews:{product_id}:{status.value if status else 'all'}:{limit}:{offset}"

        # Try cache first
        if use_cache:
            cached = await self.cache_service.get(cache_key)
            if cached is not None:
                return cached

        # Get from database
        reviews = await self.review_repository.get_by_product(
            product_id=product_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        # Cache results
        await self.cache_service.set(cache_key, reviews, self.CACHE_TTL_REVIEWS)

        return reviews

    async def get_product_rating(
        self, product_id: str, use_cache: bool = True
    ) -> float:
        """
        Get average rating for a product

        Args:
            product_id: Product identifier
            use_cache: Whether to use cache

        Returns:
            Average rating (0.0 if no reviews)
        """
        cache_key = f"product:rating:{product_id}"

        # Try cache first
        if use_cache:
            cached = await self.cache_service.get(cache_key)
            if cached is not None:
                return cached

        # Get from database
        rating = await self.review_repository.get_average_rating(product_id)

        # Cache result
        await self.cache_service.set(cache_key, rating, self.CACHE_TTL_RATINGS)

        return rating

    async def get_rating_stats(
        self, product_id: str, use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed rating statistics

        Args:
            product_id: Product identifier
            use_cache: Whether to use cache

        Returns:
            Dictionary with average_rating, total_reviews, rating_distribution
        """
        cache_key = f"product:stats:{product_id}"

        # Try cache first
        if use_cache:
            cached = await self.cache_service.get(cache_key)
            if cached is not None:
                return cached

        # Get from database
        stats = await self.review_repository.get_rating_stats(product_id)

        # Cache result
        await self.cache_service.set(cache_key, stats, self.CACHE_TTL_RATINGS)

        return stats

    async def approve_review(self, review_id: str) -> Review:
        """
        Approve a pending review

        Args:
            review_id: Review identifier

        Returns:
            Approved review
        """
        # Get review
        review = await self.review_repository.get_by_id(review_id)
        if review is None:
            raise ValueError(f"Review {review_id} not found")

        # Approve it
        review.approve()

        # Update in database
        updated_review = await self.review_repository.update(review)

        # Invalidate cache
        await self._invalidate_product_cache(updated_review.product_id)

        # Publish event
        await self.event_bus.publish(
            "review.approved",
            {
                "review_id": updated_review.id,
                "product_id": updated_review.product_id,
                "customer_id": updated_review.customer_id,
                "approved_at": updated_review.updated_at.isoformat(),
            },
        )

        return updated_review

    async def reject_review(self, review_id: str) -> Review:
        """
        Reject a review

        Args:
            review_id: Review identifier

        Returns:
            Rejected review
        """
        review = await self.review_repository.get_by_id(review_id)
        if review is None:
            raise ValueError(f"Review {review_id} not found")

        review.reject()

        updated_review = await self.review_repository.update(review)

        await self._invalidate_product_cache(updated_review.product_id)

        await self.event_bus.publish(
            "review.rejected",
            {
                "review_id": updated_review.id,
                "product_id": updated_review.product_id,
                "rejected_at": updated_review.updated_at.isoformat(),
            },
        )

        return updated_review

    async def flag_review(self, review_id: str) -> Review:
        """
        Flag a review for moderation

        Args:
            review_id: Review identifier

        Returns:
            Flagged review
        """
        review = await self.review_repository.get_by_id(review_id)
        if review is None:
            raise ValueError(f"Review {review_id} not found")

        review.flag()

        updated_review = await self.review_repository.update(review)

        await self._invalidate_product_cache(updated_review.product_id)

        await self.event_bus.publish(
            "review.flagged",
            {
                "review_id": updated_review.id,
                "product_id": updated_review.product_id,
                "flagged_at": updated_review.updated_at.isoformat(),
            },
        )

        return updated_review

    async def mark_helpful(self, review_id: str) -> Review:
        """
        Mark a review as helpful

        Args:
            review_id: Review identifier

        Returns:
            Updated review
        """
        review = await self.review_repository.get_by_id(review_id)
        if review is None:
            raise ValueError(f"Review {review_id} not found")

        review.increment_helpful()

        updated_review = await self.review_repository.update(review)

        # Note: We don't invalidate cache for helpful count updates
        # to reduce cache churn. Cache will naturally expire.

        return updated_review

    async def _invalidate_product_cache(self, product_id: str) -> None:
        """
        Invalidate all cache entries for a product

        Args:
            product_id: Product identifier
        """
        await self.cache_service.delete(f"product:reviews:{product_id}")
        await self.cache_service.delete(f"product:rating:{product_id}")
        await self.cache_service.delete(f"product:stats:{product_id}")
        # Also clear any paginated review caches
        await self.cache_service.clear(f"product:reviews:{product_id}:*")
