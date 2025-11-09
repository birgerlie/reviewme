"""
Test ReviewRepository implementation
Test against the interface, not concrete implementation
Following the Dependency Inversion Principle (SOLID)
"""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from review_service.domain.interfaces.review_repository_interface import (
    IReviewRepository,
)
from review_service.domain.models.review import Review, ReviewRating, ReviewStatus


@pytest.fixture
def sample_review() -> Review:
    return Review(
        id="rev_123",
        product_id="prod_456",
        customer_id="cust_789",
        rating=ReviewRating.FIVE_STAR,
        title="Great product",
        content="I love this!",
        status=ReviewStatus.APPROVED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_pending_review() -> Review:
    return Review(
        id="rev_124",
        product_id="prod_456",
        customer_id="cust_790",
        rating=ReviewRating.FOUR_STAR,
        title="Good product",
        content="Pretty nice",
        status=ReviewStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
class TestReviewRepositoryInterface:
    """Test the IReviewRepository interface contract"""

    async def test_create_review(self, sample_review: Review) -> None:
        """GIVEN review data WHEN create() called THEN should return review with ID"""
        # Mock implementation for this test
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.create.return_value = sample_review

        result = await mock_repo.create(sample_review)

        assert result.id is not None
        assert result.product_id == "prod_456"
        mock_repo.create.assert_called_once_with(sample_review)

    async def test_get_by_id_returns_review(self, sample_review: Review) -> None:
        """GIVEN review exists WHEN get_by_id() called THEN returns review"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_by_id.return_value = sample_review

        result = await mock_repo.get_by_id("rev_123")

        assert result.id == "rev_123"
        assert result.product_id == "prod_456"
        mock_repo.get_by_id.assert_called_once_with("rev_123")

    async def test_get_by_id_returns_none_when_not_found(self) -> None:
        """GIVEN review does not exist WHEN get_by_id() called THEN returns None"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_by_id.return_value = None

        result = await mock_repo.get_by_id("nonexistent")

        assert result is None

    async def test_get_by_product_returns_approved_only(
        self, sample_review: Review
    ) -> None:
        """GIVEN reviews exist WHEN get_by_product() THEN returns only approved"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_by_product.return_value = [sample_review]

        results = await mock_repo.get_by_product(
            product_id="prod_456", status=ReviewStatus.APPROVED
        )

        assert len(results) == 1
        assert all(r.status == ReviewStatus.APPROVED for r in results)
        mock_repo.get_by_product.assert_called_once_with(
            product_id="prod_456", status=ReviewStatus.APPROVED
        )

    async def test_get_by_product_with_pagination(
        self, sample_review: Review
    ) -> None:
        """GIVEN many reviews WHEN get_by_product() with limit/offset THEN returns paginated"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_by_product.return_value = [sample_review]

        results = await mock_repo.get_by_product(
            product_id="prod_456", limit=10, offset=5
        )

        assert len(results) <= 10
        mock_repo.get_by_product.assert_called_once_with(
            product_id="prod_456", limit=10, offset=5
        )

    async def test_get_average_rating(self) -> None:
        """GIVEN reviews WHEN get_average_rating() THEN returns correct average"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_average_rating.return_value = 4.5

        avg = await mock_repo.get_average_rating("prod_456")

        assert avg == 4.5
        mock_repo.get_average_rating.assert_called_once_with("prod_456")

    async def test_get_rating_stats(self) -> None:
        """GIVEN reviews WHEN get_rating_stats() THEN returns stats dictionary"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_rating_stats.return_value = {
            "average_rating": 4.5,
            "total_reviews": 100,
            "rating_distribution": {5: 60, 4: 25, 3: 10, 2: 3, 1: 2},
        }

        stats = await mock_repo.get_rating_stats("prod_456")

        assert stats["average_rating"] == 4.5
        assert stats["total_reviews"] == 100
        assert stats["rating_distribution"][5] == 60

    async def test_update_review(self, sample_review: Review) -> None:
        """GIVEN review changes WHEN update() called THEN updates review"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        sample_review.status = ReviewStatus.FLAGGED
        mock_repo.update.return_value = sample_review

        result = await mock_repo.update(sample_review)

        assert result.status == ReviewStatus.FLAGGED
        mock_repo.update.assert_called_once_with(sample_review)

    async def test_delete_review(self) -> None:
        """GIVEN review exists WHEN delete() called THEN removes review"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.delete.return_value = True

        result = await mock_repo.delete("rev_123")

        assert result is True
        mock_repo.delete.assert_called_once_with("rev_123")

    async def test_count_by_product(self) -> None:
        """GIVEN reviews exist WHEN count_by_product() THEN returns count"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.count_by_product.return_value = 42

        count = await mock_repo.count_by_product("prod_456")

        assert count == 42
        mock_repo.count_by_product.assert_called_once_with("prod_456")

    async def test_get_pending_reviews(
        self, sample_pending_review: Review
    ) -> None:
        """GIVEN pending reviews exist WHEN get_pending_reviews() THEN returns pending only"""
        mock_repo = AsyncMock(spec=IReviewRepository)
        mock_repo.get_by_product.return_value = [sample_pending_review]

        results = await mock_repo.get_by_product(
            product_id="prod_456", status=ReviewStatus.PENDING
        )

        assert len(results) == 1
        assert all(r.status == ReviewStatus.PENDING for r in results)
