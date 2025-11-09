"""
Test the Review domain model
Following TDD: Write this test first, then implement Review class
"""
import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add the services directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from review_service.domain.models.review import (
    Review,
    ReviewRating,
    ReviewStatus,
)


class TestReviewModel:
    def test_create_review_with_required_fields(self) -> None:
        """GIVEN valid review data WHEN creating Review THEN should succeed"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FIVE_STAR,
            title="Great product",
            content="I love this product!",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert review.product_id == "prod_456"
        assert review.rating == ReviewRating.FIVE_STAR
        assert review.status == ReviewStatus.PENDING

    def test_approve_review_changes_status(self) -> None:
        """GIVEN pending review WHEN approve() called THEN status changes to approved"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FOUR_STAR,
            title="Good",
            content="Nice product",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        review.approve()

        assert review.status == ReviewStatus.APPROVED

    def test_cannot_approve_already_approved_review(self) -> None:
        """GIVEN approved review WHEN approve() called THEN should not change"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FIVE_STAR,
            title="Great",
            content="Excellent",
            status=ReviewStatus.APPROVED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        original_updated_at = review.updated_at
        review.approve()

        # Should not change if already approved
        assert review.status == ReviewStatus.APPROVED

    def test_increment_helpful_count(self) -> None:
        """GIVEN review WHEN increment_helpful() THEN count increases"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FIVE_STAR,
            title="Great",
            content="Love it",
            status=ReviewStatus.APPROVED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            helpful_count=5,
        )

        review.increment_helpful()

        assert review.helpful_count == 6

    def test_flag_review_changes_status_to_flagged(self) -> None:
        """GIVEN approved review WHEN flag() called THEN status changes to flagged"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.THREE_STAR,
            title="Okay",
            content="It's fine",
            status=ReviewStatus.APPROVED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        review.flag()

        assert review.status == ReviewStatus.FLAGGED

    def test_reject_review_changes_status_to_rejected(self) -> None:
        """GIVEN pending review WHEN reject() called THEN status changes to rejected"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.ONE_STAR,
            title="Bad",
            content="Terrible",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        review.reject()

        assert review.status == ReviewStatus.REJECTED

    def test_review_with_verified_purchase(self) -> None:
        """GIVEN verified purchase WHEN creating review THEN verified_purchase is True"""
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FIVE_STAR,
            title="Great",
            content="Love it",
            status=ReviewStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            verified_purchase=True,
        )

        assert review.verified_purchase is True

    def test_review_with_media_urls(self) -> None:
        """GIVEN review with media WHEN creating review THEN media_urls stored"""
        media_urls = ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FIVE_STAR,
            title="Great with photos",
            content="See photos",
            status=ReviewStatus.APPROVED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            media_urls=media_urls,
        )

        assert review.media_urls == media_urls
        assert len(review.media_urls) == 2

    def test_review_with_attributes(self) -> None:
        """GIVEN review with custom attributes WHEN creating review THEN attributes stored"""
        attributes = {"size": "Large", "color": "Blue", "fit": "True to size"}
        review = Review(
            id="rev_123",
            product_id="prod_456",
            customer_id="cust_789",
            rating=ReviewRating.FOUR_STAR,
            title="Good",
            content="Nice",
            status=ReviewStatus.APPROVED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            attributes=attributes,
        )

        assert review.attributes == attributes
        assert review.attributes["size"] == "Large"

    def test_all_rating_values_are_valid(self) -> None:
        """GIVEN all rating enum values WHEN used THEN all are valid"""
        assert ReviewRating.ONE_STAR.value == 1
        assert ReviewRating.TWO_STAR.value == 2
        assert ReviewRating.THREE_STAR.value == 3
        assert ReviewRating.FOUR_STAR.value == 4
        assert ReviewRating.FIVE_STAR.value == 5

    def test_all_status_values_exist(self) -> None:
        """GIVEN all status enum values WHEN accessed THEN all exist"""
        statuses = [
            ReviewStatus.PENDING,
            ReviewStatus.APPROVED,
            ReviewStatus.REJECTED,
            ReviewStatus.FLAGGED,
        ]
        assert len(statuses) == 4
