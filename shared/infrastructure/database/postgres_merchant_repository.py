"""
PostgreSQL Merchant Repository Implementation
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
import uuid

from shared.domain.entities.merchant import Merchant, MerchantPlan
from shared.domain.interfaces.merchant_repository_interface import IMerchantRepository
from shared.infrastructure.database.models import MerchantModel


class PostgresMerchantRepository(IMerchantRepository):
    """
    PostgreSQL implementation of merchant repository
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    def _to_entity(self, model: MerchantModel) -> Merchant:
        """Convert database model to domain entity"""
        return Merchant(
            id=model.id,
            email=model.email,
            company_name=model.company_name,
            api_key=model.api_key,
            active=model.active,
            plan=MerchantPlan(model.plan),
            created_at=model.created_at,
            updated_at=model.updated_at,
            settings=model.settings or {},
        )

    def _to_model(self, entity: Merchant) -> MerchantModel:
        """Convert domain entity to database model"""
        return MerchantModel(
            id=entity.id or str(uuid.uuid4()),
            email=entity.email,
            company_name=entity.company_name,
            api_key=entity.api_key or Merchant.generate_api_key(),
            active=entity.active,
            plan=entity.plan.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            settings=entity.settings,
        )

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
        # Check if email already exists
        existing = await self.get_by_email(merchant.email)
        if existing:
            raise ValueError(f"Merchant with email {merchant.email} already exists")

        # Generate ID and API key if not provided
        if not merchant.id:
            merchant.id = str(uuid.uuid4())
        if not merchant.api_key:
            merchant.api_key = Merchant.generate_api_key()

        # Set timestamps
        now = datetime.utcnow()
        merchant.created_at = now
        merchant.updated_at = now

        # Convert to model and save
        model = self._to_model(merchant)
        self.session.add(model)
        await self.session.flush()

        return merchant

    async def get_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Get merchant by ID"""
        stmt = select(MerchantModel).where(MerchantModel.id == merchant_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def get_by_email(self, email: str) -> Optional[Merchant]:
        """Get merchant by email address"""
        stmt = select(MerchantModel).where(MerchantModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def get_by_api_key(self, api_key: str) -> Optional[Merchant]:
        """
        Get merchant by API key (for authentication)

        Returns:
            Merchant if found and active, None otherwise
        """
        stmt = select(MerchantModel).where(
            MerchantModel.api_key == api_key,
            MerchantModel.active == True
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

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
        # Check if merchant exists
        existing = await self.get_by_id(merchant.id)
        if not existing:
            raise ValueError(f"Merchant {merchant.id} not found")

        # Update timestamp
        merchant.updated_at = datetime.utcnow()

        # Update in database
        stmt = (
            update(MerchantModel)
            .where(MerchantModel.id == merchant.id)
            .values(
                email=merchant.email,
                company_name=merchant.company_name,
                api_key=merchant.api_key,
                active=merchant.active,
                plan=merchant.plan.value,
                updated_at=merchant.updated_at,
                settings=merchant.settings,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return merchant

    async def delete(self, merchant_id: str) -> bool:
        """
        Delete merchant (soft delete by deactivating)

        Args:
            merchant_id: Merchant identifier

        Returns:
            True if deleted, False if not found
        """
        merchant = await self.get_by_id(merchant_id)
        if not merchant:
            return False

        merchant.deactivate()
        await self.update(merchant)
        return True

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Merchant]:
        """
        List all merchants (paginated)

        Args:
            limit: Maximum merchants to return
            offset: Number of merchants to skip

        Returns:
            List of merchants
        """
        stmt = (
            select(MerchantModel)
            .order_by(MerchantModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def count_by_plan(self, plan: str) -> int:
        """
        Count merchants by plan

        Args:
            plan: Plan name (free, basic, pro, enterprise)

        Returns:
            Count of merchants on that plan
        """
        stmt = select(func.count(MerchantModel.id)).where(MerchantModel.plan == plan)
        result = await self.session.execute(stmt)
        return result.scalar_one()
