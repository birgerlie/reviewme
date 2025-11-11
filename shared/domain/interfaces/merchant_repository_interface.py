"""
Merchant Repository Interface
Defines the contract for merchant data access
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from shared.domain.entities.merchant import Merchant


class IMerchantRepository(ABC):
    """
    Merchant Repository Interface

    Defines methods for merchant data access following the Repository pattern.
    Implementations handle actual data persistence (PostgreSQL, etc.)
    """

    @abstractmethod
    async def create(self, merchant: Merchant) -> Merchant:
        """
        Create a new merchant

        Args:
            merchant: Merchant entity to create

        Returns:
            Created merchant with generated ID

        Raises:
            ValueError: If merchant with same email already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """
        Get merchant by ID

        Args:
            merchant_id: Merchant identifier

        Returns:
            Merchant if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Merchant]:
        """
        Get merchant by email address

        Args:
            email: Merchant email

        Returns:
            Merchant if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Optional[Merchant]:
        """
        Get merchant by API key (for authentication)

        Args:
            api_key: API key

        Returns:
            Merchant if found and active, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, merchant: Merchant) -> Merchant:
        """
        Update existing merchant

        Args:
            merchant: Merchant entity with updated data

        Returns:
            Updated merchant

        Raises:
            ValueError: If merchant not found
        """
        pass

    @abstractmethod
    async def delete(self, merchant_id: str) -> bool:
        """
        Delete merchant (soft delete by deactivating)

        Args:
            merchant_id: Merchant identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Merchant]:
        """
        List all merchants (paginated)

        Args:
            limit: Maximum merchants to return
            offset: Number of merchants to skip

        Returns:
            List of merchants
        """
        pass

    @abstractmethod
    async def count_by_plan(self, plan: str) -> int:
        """
        Count merchants by plan

        Args:
            plan: Plan name (free, basic, pro, enterprise)

        Returns:
            Count of merchants on that plan
        """
        pass
