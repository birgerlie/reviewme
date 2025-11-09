"""
Review Service Client Interface
Interface for communicating with the Review Service
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IReviewServiceClient(ABC):
    """
    Abstract base class for Review Service Client

    This interface defines how the Widget Service communicates
    with the Review Service to fetch review data.
    """

    @abstractmethod
    async def get_reviews(
        self, product_id: str, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get reviews for a product from Review Service

        Args:
            product_id: Product identifier
            limit: Maximum number of reviews
            offset: Pagination offset

        Returns:
            List of review dictionaries
        """
        pass

    @abstractmethod
    async def get_rating(self, product_id: str) -> Dict[str, Any]:
        """
        Get rating summary for a product from Review Service

        Args:
            product_id: Product identifier

        Returns:
            Dict with average_rating and total_reviews
        """
        pass
