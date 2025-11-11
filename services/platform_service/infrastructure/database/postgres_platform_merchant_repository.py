"""
PostgreSQL Platform Merchant Repository Implementation
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
import uuid

from platform_service.domain.entities.platform_merchant import PlatformMerchant, PlatformType
from platform_service.infrastructure.database.models import PlatformMerchantModel


class IPlatformMerchantRepository:
    """
    Platform Merchant Repository Interface
    """
    async def create(self, merchant: PlatformMerchant) -> PlatformMerchant:
        pass

    async def get_by_id(self, merchant_id: str) -> Optional[PlatformMerchant]:
        pass

    async def get_by_platform_domain(self, platform: PlatformType, domain: str) -> Optional[PlatformMerchant]:
        pass

    async def update(self, merchant: PlatformMerchant) -> PlatformMerchant:
        pass

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[PlatformMerchant]:
        pass


class PostgresPlatformMerchantRepository(IPlatformMerchantRepository):
    """
    PostgreSQL implementation of platform merchant repository
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    def _to_entity(self, model: PlatformMerchantModel) -> PlatformMerchant:
        """Convert database model to domain entity"""
        return PlatformMerchant(
            id=model.id,
            platform=PlatformType(model.platform),
            platform_domain=model.platform_domain,
            platform_merchant_id=model.platform_merchant_id,
            access_token=model.access_token,
            scopes=model.scopes or [],
            token_expires_at=model.token_expires_at,
            store_name=model.store_name,
            email=model.email,
            currency=model.currency,
            timezone=model.timezone,
            installed_at=model.installed_at,
            active=model.active,
            widget_config=model.widget_config or {},
            platform_metadata=model.platform_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: PlatformMerchant) -> PlatformMerchantModel:
        """Convert domain entity to database model"""
        return PlatformMerchantModel(
            id=entity.id or str(uuid.uuid4()),
            platform=entity.platform.value,
            platform_domain=entity.platform_domain,
            platform_merchant_id=entity.platform_merchant_id,
            access_token=entity.access_token,
            scopes=entity.scopes,
            token_expires_at=entity.token_expires_at,
            store_name=entity.store_name,
            email=entity.email,
            currency=entity.currency,
            timezone=entity.timezone,
            installed_at=entity.installed_at,
            active=entity.active,
            widget_config=entity.widget_config,
            platform_metadata=entity.platform_metadata,
            created_at=entity.created_at or datetime.utcnow(),
            updated_at=entity.updated_at or datetime.utcnow(),
        )

    async def create(self, merchant: PlatformMerchant) -> PlatformMerchant:
        """
        Create a new platform merchant

        Args:
            merchant: PlatformMerchant entity to create

        Returns:
            Created merchant with generated ID

        Raises:
            ValueError: If merchant with same platform + domain already exists
        """
        # Check if platform merchant already exists
        existing = await self.get_by_platform_domain(
            merchant.platform, merchant.platform_domain
        )
        if existing:
            raise ValueError(
                f"Merchant already exists for {merchant.platform.value}: {merchant.platform_domain}"
            )

        # Generate ID if not provided
        if not merchant.id:
            merchant.id = str(uuid.uuid4())

        # Set timestamps
        now = datetime.utcnow()
        if not merchant.created_at:
            merchant.created_at = now
        if not merchant.updated_at:
            merchant.updated_at = now

        # Validate
        merchant.validate()

        # Convert to model and save
        model = self._to_model(merchant)
        self.session.add(model)
        await self.session.flush()

        return merchant

    async def get_by_id(self, merchant_id: str) -> Optional[PlatformMerchant]:
        """Get platform merchant by ID"""
        stmt = select(PlatformMerchantModel).where(PlatformMerchantModel.id == merchant_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def get_by_platform_domain(
        self, platform: PlatformType, domain: str
    ) -> Optional[PlatformMerchant]:
        """
        Get platform merchant by platform and domain

        Args:
            platform: Platform type
            domain: Shop/store domain

        Returns:
            PlatformMerchant if found, None otherwise
        """
        stmt = select(PlatformMerchantModel).where(
            and_(
                PlatformMerchantModel.platform == platform.value,
                PlatformMerchantModel.platform_domain == domain
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def update(self, merchant: PlatformMerchant) -> PlatformMerchant:
        """
        Update existing platform merchant

        Args:
            merchant: PlatformMerchant entity with updated data

        Returns:
            Updated merchant

        Raises:
            ValueError: If merchant not found
        """
        # Check if merchant exists
        existing = await self.get_by_id(merchant.id)
        if not existing:
            raise ValueError(f"Platform merchant {merchant.id} not found")

        # Update timestamp
        merchant.updated_at = datetime.utcnow()

        # Update in database
        stmt = (
            update(PlatformMerchantModel)
            .where(PlatformMerchantModel.id == merchant.id)
            .values(
                access_token=merchant.access_token,
                scopes=merchant.scopes,
                token_expires_at=merchant.token_expires_at,
                store_name=merchant.store_name,
                email=merchant.email,
                currency=merchant.currency,
                timezone=merchant.timezone,
                active=merchant.active,
                widget_config=merchant.widget_config,
                platform_metadata=merchant.platform_metadata,
                updated_at=merchant.updated_at,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return merchant

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[PlatformMerchant]:
        """
        List all platform merchants (paginated)

        Args:
            limit: Maximum merchants to return
            offset: Number of merchants to skip

        Returns:
            List of platform merchants
        """
        stmt = (
            select(PlatformMerchantModel)
            .order_by(PlatformMerchantModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]
