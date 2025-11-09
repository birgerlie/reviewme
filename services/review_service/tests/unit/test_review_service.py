"""
Test ReviewService business logic
This is where business rules live
Following TDD: Write tests first
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from review_service.domain.services.review_service import ReviewService
from review_service.domain.models.review import Review, ReviewRating, ReviewStatus


@pytest.fixture
def mock_review_repo():
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_product = AsyncMock()
    repo.get_average_rating = AsyncMock()
    repo.get_rating_stats = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.count_by_product = AsyncMock()
    return repo


@pytest.fixture
def mock_cache():
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.clear = AsyncMock()
    return cache


@pytest.fixture
def mock_event_bus():
    bus = Mock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def review_service(mock_review_repo, mock_cache, mock_event_bus):
    return ReviewService(
        review_repository=mock_review_repo,
        cache_service=mock_cache,
        event_bus=mock_event_bus,
    )


@pytest.mark.asyncio
class TestReviewService:
    """Test ReviewService business logic"""

    async def test_auto_approve_verified_high_rating(
        self, review_service, mock_review_repo, mock_event_bus
    ) -> None:
        """
        Business Rule: Verified purchases with 4+ stars auto-approve
        GIVEN verified purchase with 5 stars
        WHEN create_review called
        THEN status should be APPROVED
        """
        review = Review(
            id=None,
            product_id="prod_123",
            customer_id="cust_456",
            rating=ReviewRating.FIVE_STAR,
            title="Excellent",
            content="Great product",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            verified_purchase=True,
        )

        approved_review = Review(
            id="rev_123",
            product_id="prod_123",
            customer_id="cust_456",
            rating=ReviewRating.FIVE_STAR,
            title="Excellent",
            content="Great product",
            status=ReviewStatus.APPROVED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            verified_purchase=True,
        )

        mock_review_repo.create.return_value = approved_review

        result = await review_service.create_review(review)

        assert result.status == ReviewStatus.APPROVED
        # Verify event was published
        mock_event_bus.publish.assert_called()

    async def test_unverified_purchase_stays_pending(
        self, review_service, mock_review_repo
    ) -> None:
        """
        Business Rule: Unverified purchases need manual approval
        GIVEN unverified purchase
        WHEN create_review called
        THEN status should remain PENDING
        """
        review = Review(
            id=None,
            product_id="prod_123",
            customer_id="cust_456",
            rating=ReviewRating.FIVE_STAR,
            title="Great",
            content="Love it",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            verified_purchase=False,
        )

        mock_review_repo.create.return_value = Review(
            **{**review.__dict__, "id": "rev_123"}
        )

        result = await review_service.create_review(review)

        assert result.status == ReviewStatus.PENDING

    async def test_low_rating_verified_stays_pending(
        self, review_service, mock_review_repo
    ) -> None:
        """
        Business Rule: Verified purchases with < 4 stars need manual approval
        GIVEN verified purchase with 3 stars
        WHEN create_review called
        THEN status should remain PENDING
        """
        review = Review(
            id=None,
            product_id="prod_123",
            customer_id="cust_456",
            rating=ReviewRating.THREE_STAR,
            title="Okay",
            content="It's fine",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            verified_purchase=True,
        )

        mock_review_repo.create.return_value = Review(
            **{**review.__dict__, "id": "rev_123"}
        )

        result = await review_service.create_review(review)

        assert result.status == ReviewStatus.PENDING

    async def test_cache_invalidation_on_create(
        self, review_service, mock_cache, mock_review_repo
    ) -> None:
        """
        GIVEN new review created
        WHEN create_review called
        THEN product cache should be invalidated
        """
        review = Review(
            id=None,
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FOUR_STAR,
            title="Good",
            content="Nice",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            verified_purchase=False,
        )

        mock_review_repo.create.return_value = Review(
            **{**review.__dict__, "id": "rev_123"}
        )

        await review_service.create_review(review)

        # Verify cache was invalidated
        mock_cache.delete.assert_any_call("product:reviews:prod_456")
        mock_cache.delete.assert_any_call("product:rating:prod_456")

    async def test_get_reviews_uses_cache(
        self, review_service, mock_cache, mock_review_repo
    ) -> None:
        """
        Performance optimization: Use cache when available
        GIVEN reviews in cache
        WHEN get_product_reviews called
        THEN should return cached data without DB query
        """
        cached_reviews = [
            Review(
                id="rev_123",
                product_id="prod_123",
                customer_id="cust_456",
                rating=ReviewRating.FIVE_STAR,
                title="Great",
                content="Love it",
                status=ReviewStatus.APPROVED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        ]
        mock_cache.get.return_value = cached_reviews

        result = await review_service.get_product_reviews(
            product_id="prod_123", use_cache=True
        )

        assert result == cached_reviews
        mock_review_repo.get_by_product.assert_not_called()

    async def test_get_reviews_caches_db_results(
        self, review_service, mock_cache, mock_review_repo
    ) -> None:
        """
        GIVEN reviews not in cache
        WHEN get_product_reviews called
        THEN should query DB and cache results
        """
        mock_cache.get.return_value = None
        db_reviews = [
            Review(
                id="rev_123",
                product_id="prod_123",
                customer_id="cust_456",
                rating=ReviewRating.FIVE_STAR,
                title="Great",
                content="Love it",
                status=ReviewStatus.APPROVED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        ]
        mock_review_repo.get_by_product.return_value = db_reviews

        result = await review_service.get_product_reviews("prod_123")

        assert result == db_reviews
        mock_cache.set.assert_called_once()

    async def test_get_rating_uses_cache(
        self, review_service, mock_cache, mock_review_repo
    ) -> None:
        """
        GIVEN rating in cache
        WHEN get_product_rating called
        THEN should return cached data
        """
        mock_cache.get.return_value = 4.5

        result = await review_service.get_product_rating("prod_123")

        assert result == 4.5
        mock_review_repo.get_average_rating.assert_not_called()

    async def test_approve_review_publishes_event(
        self, review_service, mock_review_repo, mock_event_bus
    ) -> None:
        """
        GIVEN pending review
        WHEN approve_review called
        THEN should publish review.approved event
        """
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FOUR_STAR,
            title="Good",
            content="Nice",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_review_repo.get_by_id.return_value = review
        mock_review_repo.update.return_value = Review(
            **{**review.__dict__, "status": ReviewStatus.APPROVED}
        )

        await review_service.approve_review("rev_123")

        # Verify event was published
        mock_event_bus.publish.assert_called()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "review.approved"

    async def test_get_rating_stats_returns_complete_data(
        self, review_service, mock_review_repo, mock_cache
    ) -> None:
        """
        GIVEN product with reviews
        WHEN get_rating_stats called
        THEN returns complete statistics
        """
        stats = {
            "average_rating": 4.5,
            "total_reviews": 100,
            "rating_distribution": {5: 60, 4: 25, 3: 10, 2: 3, 1: 2},
        }
        mock_cache.get.return_value = None
        mock_review_repo.get_rating_stats.return_value = stats

        result = await review_service.get_rating_stats("prod_123")

        assert result["average_rating"] == 4.5
        assert result["total_reviews"] == 100
        assert sum(result["rating_distribution"].values()) == 100
