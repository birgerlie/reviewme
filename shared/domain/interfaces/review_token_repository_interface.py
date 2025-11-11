"""
Review Token Repository Interface
Defines the contract for review token data access
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from shared.domain.entities.review_token import ReviewToken


class IReviewTokenRepository(ABC):
    """
    Review Token Repository Interface

    Defines methods for review token data access following the Repository pattern.
    Implementations handle actual data persistence (PostgreSQL, etc.)
    """

    @abstractmethod
    async def create(self, token: ReviewToken) -> ReviewToken:
        """
        Create a new review token

        Args:
            token: ReviewToken entity to create

        Returns:
            Created token with generated ID

        Raises:
            ValueError: If token with same token string already exists
        """
        pass

    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[ReviewToken]:
        """
        Get token by token string

        Args:
            token: Token string (e.g., "rt_abc123...")

        Returns:
            ReviewToken if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_id(self, token_id: str) -> Optional[ReviewToken]:
        """
        Get token by ID

        Args:
            token_id: Token identifier

        Returns:
            ReviewToken if found, None otherwise
        """
        pass

    @abstractmethod
    async def mark_as_used(self, token: str) -> bool:
        """
        Mark token as used (atomic operation)

        This must be atomic to prevent race conditions where
        two reviews are submitted with the same token.

        Args:
            token: Token string

        Returns:
            True if marked as used, False if token not found or already used

        Implementation note:
        Use database-level atomic UPDATE with WHERE clause:
        UPDATE review_tokens SET used=true, used_at=NOW()
        WHERE token=? AND used=false
        RETURNING id
        """
        pass

    @abstractmethod
    async def delete_expired(self, current_time: Optional = None) -> int:
        """
        Delete expired tokens (cleanup task)

        Args:
            current_time: Optional current time (for testing)

        Returns:
            Number of tokens deleted
        """
        pass

    @abstractmethod
    async def list_by_merchant(
        self, merchant_id: str, limit: int = 100, offset: int = 0
    ) -> List[ReviewToken]:
        """
        List tokens for a merchant (for admin dashboard)

        Args:
            merchant_id: Merchant identifier
            limit: Maximum tokens to return
            offset: Number of tokens to skip

        Returns:
            List of tokens
        """
        pass

    @abstractmethod
    async def list_by_customer(
        self, customer_email: str, merchant_id: str
    ) -> List[ReviewToken]:
        """
        List tokens for a customer (to check if already sent)

        Args:
            customer_email: Customer email address
            merchant_id: Merchant identifier

        Returns:
            List of tokens for this customer
        """
        pass

    @abstractmethod
    async def count_unused_by_product(
        self, merchant_id: str, product_id: str
    ) -> int:
        """
        Count unused tokens for a product

        Args:
            merchant_id: Merchant identifier
            product_id: Product identifier

        Returns:
            Count of unused, non-expired tokens
        """
        pass
