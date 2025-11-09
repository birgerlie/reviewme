"""
Review Repository Interface
Defines the contract for review data access
Following the Dependency Inversion Principle (SOLID)
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from review_service.domain.models.review import Review, ReviewStatus


class IReviewRepository(ABC):
    """
    Abstract base class for Review Repository

    This interface defines all data access operations for reviews.
    Concrete implementations can use PostgreSQL, MongoDB, or any other storage.

    Benefits:
    - Allows easy swapping of database implementations
    - Makes testing easier with mocks
    - Decouples domain logic from infrastructure
    """

    @abstractmethod
    async def create(self, review: Review) -> Review:
        """
        Create a new review

        Args:
            review: Review domain model

        Returns:
            Review: Created review with generated ID

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, review_id: str) -> Optional[Review]:
        """
        Get review by ID

        Args:
            review_id: Unique review identifier

        Returns:
            Optional[Review]: Review if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_product(
        self,
        product_id: str,
        status: Optional[ReviewStatus] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Review]:
        """
        Get reviews for a product with optional filtering

        Args:
            product_id: Product identifier
            status: Optional status filter (e.g., only APPROVED reviews)
            limit: Maximum number of reviews to return
            offset: Number of reviews to skip (for pagination)

        Returns:
            List[Review]: List of reviews, may be empty
        """
        pass

    @abstractmethod
    async def get_average_rating(self, product_id: str) -> float:
        """
        Calculate average rating for a product

        Args:
            product_id: Product identifier

        Returns:
            float: Average rating (0.0 if no reviews)
        """
        pass

    @abstractmethod
    async def get_rating_stats(self, product_id: str) -> Dict[str, Any]:
        """
        Get detailed rating statistics for a product

        Args:
            product_id: Product identifier

        Returns:
            Dict with keys:
            - average_rating: float
            - total_reviews: int
            - rating_distribution: Dict[int, int] (rating -> count)
        """
        pass

    @abstractmethod
    async def update(self, review: Review) -> Review:
        """
        Update an existing review

        Args:
            review: Review with updated fields

        Returns:
            Review: Updated review

        Raises:
            RepositoryError: If review not found or update fails
        """
        pass

    @abstractmethod
    async def delete(self, review_id: str) -> bool:
        """
        Delete a review

        Args:
            review_id: Review identifier

        Returns:
            bool: True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_by_product(
        self, product_id: str, status: Optional[ReviewStatus] = None
    ) -> int:
        """
        Count reviews for a product

        Args:
            product_id: Product identifier
            status: Optional status filter

        Returns:
            int: Number of reviews
        """
        pass
