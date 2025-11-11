"""
Review domain model
This is the core business entity for reviews
Implements domain logic and business rules
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any


class ReviewRating(Enum):
    """Review rating from 1 to 5 stars"""

    ONE_STAR = 1
    TWO_STAR = 2
    THREE_STAR = 3
    FOUR_STAR = 4
    FIVE_STAR = 5


class ReviewStatus(Enum):
    """Review moderation status"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


@dataclass
class Review:
    """
    Review domain model

    This class represents a customer review and contains all business logic
    related to review state management and validation.

    Business Rules:
    - Reviews start in PENDING status
    - Only PENDING reviews can be approved
    - Approved reviews can be flagged for re-moderation
    - Helpful count can only increase
    - Updated timestamp changes on state transitions
    """

    # Required fields
    product_id: str
    customer_id: str
    rating: ReviewRating
    title: str
    content: str
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields
    id: Optional[str] = None
    verified_purchase: bool = False
    helpful_count: int = 0
    media_urls: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def approve(self, current_time: Optional[datetime] = None) -> None:
        """
        Approve a pending review

        Business Rule: Only PENDING reviews can be approved.
        Already approved reviews remain unchanged.

        Args:
            current_time: Optional timestamp (for testing). Defaults to utcnow()
        """
        if self.status == ReviewStatus.PENDING:
            self.status = ReviewStatus.APPROVED
            self.updated_at = current_time or datetime.utcnow()

    def reject(self, current_time: Optional[datetime] = None) -> None:
        """
        Reject a review

        Sets the review status to REJECTED

        Args:
            current_time: Optional timestamp (for testing). Defaults to utcnow()
        """
        self.status = ReviewStatus.REJECTED
        self.updated_at = current_time or datetime.utcnow()

    def flag(self, current_time: Optional[datetime] = None) -> None:
        """
        Flag a review for moderation

        Used when users report inappropriate content or when
        automated systems detect potential issues

        Args:
            current_time: Optional timestamp (for testing). Defaults to utcnow()
        """
        self.status = ReviewStatus.FLAGGED
        self.updated_at = current_time or datetime.utcnow()

    def increment_helpful(self, current_time: Optional[datetime] = None) -> None:
        """
        Increment the helpful count

        Called when users mark a review as helpful

        Args:
            current_time: Optional timestamp (for testing). Defaults to utcnow()
        """
        self.helpful_count += 1
        self.updated_at = current_time or datetime.utcnow()

    def validate(self) -> None:
        """
        Validate review data

        Raises:
            ValueError: If validation fails
        """
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id is required")

        if not self.customer_id or not self.customer_id.strip():
            raise ValueError("customer_id is required")

        if not self.title or not self.title.strip():
            raise ValueError("title is required")

        if len(self.title) > 500:
            raise ValueError("title must be 500 characters or less")

        if not self.content or not self.content.strip():
            raise ValueError("content is required")

        if len(self.content) > 5000:
            raise ValueError("content must be 5000 characters or less")

        if len(self.media_urls) > 10:
            raise ValueError("maximum 10 media files allowed")

    def is_approved(self) -> bool:
        """Check if review is approved"""
        return self.status == ReviewStatus.APPROVED

    def is_pending(self) -> bool:
        """Check if review is pending"""
        return self.status == ReviewStatus.PENDING

    def is_high_rating(self) -> bool:
        """Check if review has 4 or 5 stars (used for auto-approval)"""
        return self.rating.value >= 4

    def __repr__(self) -> str:
        return (
            f"Review(id={self.id}, product_id={self.product_id}, "
            f"rating={self.rating.value}, status={self.status.value})"
        )
