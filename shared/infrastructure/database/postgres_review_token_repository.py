"""
PostgreSQL Review Token Repository Implementation
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
import uuid

from shared.domain.entities.review_token import ReviewToken
from shared.domain.interfaces.review_token_repository_interface import IReviewTokenRepository
from shared.infrastructure.database.models import ReviewTokenModel


class PostgresReviewTokenRepository(IReviewTokenRepository):
    """
    PostgreSQL implementation of review token repository
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    def _to_entity(self, model: ReviewTokenModel) -> ReviewToken:
        """Convert database model to domain entity"""
        return ReviewToken(
            id=model.id,
            token=model.token,
            merchant_id=model.merchant_id,
            product_id=model.product_id,
            order_id=model.order_id,
            customer_email=model.customer_email,
            customer_name=model.customer_name,
            used=model.used,
            used_at=model.used_at,
            expires_at=model.expires_at,
            created_at=model.created_at,
        )

    def _to_model(self, entity: ReviewToken) -> ReviewTokenModel:
        """Convert domain entity to database model"""
        return ReviewTokenModel(
            id=entity.id or str(uuid.uuid4()),
            token=entity.token or ReviewToken.generate_token(),
            merchant_id=entity.merchant_id,
            product_id=entity.product_id,
            order_id=entity.order_id,
            customer_email=entity.customer_email,
            customer_name=entity.customer_name,
            used=entity.used,
            used_at=entity.used_at,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
        )

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
        # Generate ID and token if not provided
        if not token.id:
            token.id = str(uuid.uuid4())
        if not token.token:
            token.token = ReviewToken.generate_token()

        # Set created_at
        if not token.created_at:
            token.created_at = datetime.utcnow()

        # Validate
        token.validate()

        # Convert to model and save
        model = self._to_model(token)
        self.session.add(model)
        await self.session.flush()

        return token

    async def get_by_token(self, token: str) -> Optional[ReviewToken]:
        """Get token by token string"""
        stmt = select(ReviewTokenModel).where(ReviewTokenModel.token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def get_by_id(self, token_id: str) -> Optional[ReviewToken]:
        """Get token by ID"""
        stmt = select(ReviewTokenModel).where(ReviewTokenModel.id == token_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def mark_as_used(self, token: str) -> bool:
        """
        Mark token as used (atomic operation)

        This uses database-level atomic UPDATE to prevent race conditions
        where two reviews are submitted with the same token.

        Args:
            token: Token string

        Returns:
            True if marked as used, False if token not found or already used
        """
        # Atomic UPDATE with WHERE clause
        # Only updates if token exists AND is not used
        stmt = (
            update(ReviewTokenModel)
            .where(
                and_(
                    ReviewTokenModel.token == token,
                    ReviewTokenModel.used == False
                )
            )
            .values(
                used=True,
                used_at=datetime.utcnow()
            )
            .returning(ReviewTokenModel.id)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        # If a row was updated, the token was successfully marked as used
        return result.scalar_one_or_none() is not None

    async def delete_expired(self, current_time: Optional[datetime] = None) -> int:
        """
        Delete expired tokens (cleanup task)

        Args:
            current_time: Optional current time (for testing)

        Returns:
            Number of tokens deleted
        """
        now = current_time or datetime.utcnow()

        # Delete tokens that are expired
        stmt = delete(ReviewTokenModel).where(
            ReviewTokenModel.expires_at < now
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount

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
        stmt = (
            select(ReviewTokenModel)
            .where(ReviewTokenModel.merchant_id == merchant_id)
            .order_by(ReviewTokenModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

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
        stmt = (
            select(ReviewTokenModel)
            .where(
                and_(
                    ReviewTokenModel.customer_email == customer_email,
                    ReviewTokenModel.merchant_id == merchant_id
                )
            )
            .order_by(ReviewTokenModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

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
        now = datetime.utcnow()

        stmt = select(func.count(ReviewTokenModel.id)).where(
            and_(
                ReviewTokenModel.merchant_id == merchant_id,
                ReviewTokenModel.product_id == product_id,
                ReviewTokenModel.used == False,
                ReviewTokenModel.expires_at > now
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
