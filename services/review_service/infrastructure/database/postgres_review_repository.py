"""
PostgreSQL implementation of IReviewRepository
Uses SQLAlchemy async for database operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.exc import SQLAlchemyError

from review_service.domain.interfaces.review_repository_interface import (
    IReviewRepository,
)
from review_service.domain.models.review import Review, ReviewStatus, ReviewRating
from review_service.infrastructure.database.models import ReviewModel


class RepositoryError(Exception):
    """Custom exception for repository errors"""

    pass


class PostgresReviewRepository(IReviewRepository):
    """
    PostgreSQL implementation of review repository

    Uses SQLAlchemy async session for non-blocking database operations.
    Handles conversion between domain models and ORM models.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, review: Review) -> Review:
        """Create a new review in the database"""
        try:
            # Convert domain model to ORM model
            db_review = ReviewModel(
                product_id=review.product_id,
                customer_id=review.customer_id,
                rating=review.rating.value,
                title=review.title,
                content=review.content,
                status=review.status.value,
                verified_purchase=review.verified_purchase,
                helpful_count=review.helpful_count,
                media_urls=review.media_urls,
                attributes=review.attributes,
            )

            self.session.add(db_review)
            await self.session.commit()
            await self.session.refresh(db_review)

            # Convert back to domain model
            return self._to_domain_model(db_review)

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to create review: {str(e)}")

    async def get_by_id(self, review_id: str) -> Optional[Review]:
        """Get review by ID"""
        try:
            stmt = select(ReviewModel).where(ReviewModel.id == review_id)
            result = await self.session.execute(stmt)
            db_review = result.scalar_one_or_none()

            if db_review is None:
                return None

            return self._to_domain_model(db_review)

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get review: {str(e)}")

    async def get_by_product(
        self,
        product_id: str,
        status: Optional[ReviewStatus] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Review]:
        """Get reviews for a product with optional filtering"""
        try:
            stmt = select(ReviewModel).where(ReviewModel.product_id == product_id)

            if status is not None:
                stmt = stmt.where(ReviewModel.status == status.value)

            # Order by created_at descending (newest first)
            stmt = stmt.order_by(ReviewModel.created_at.desc())

            # Pagination
            stmt = stmt.limit(limit).offset(offset)

            result = await self.session.execute(stmt)
            db_reviews = result.scalars().all()

            return [self._to_domain_model(db_review) for db_review in db_reviews]

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get reviews: {str(e)}")

    async def get_average_rating(self, product_id: str) -> float:
        """Calculate average rating for a product"""
        try:
            stmt = (
                select(func.avg(ReviewModel.rating))
                .where(ReviewModel.product_id == product_id)
                .where(ReviewModel.status == ReviewStatus.APPROVED.value)
            )

            result = await self.session.execute(stmt)
            avg_rating = result.scalar()

            return float(avg_rating) if avg_rating is not None else 0.0

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to calculate average rating: {str(e)}")

    async def get_rating_stats(self, product_id: str) -> Dict[str, Any]:
        """Get detailed rating statistics"""
        try:
            # Get average and count
            avg_stmt = (
                select(func.avg(ReviewModel.rating), func.count(ReviewModel.id))
                .where(ReviewModel.product_id == product_id)
                .where(ReviewModel.status == ReviewStatus.APPROVED.value)
            )

            result = await self.session.execute(avg_stmt)
            avg_rating, total_reviews = result.one()

            # Get rating distribution
            dist_stmt = (
                select(ReviewModel.rating, func.count(ReviewModel.id))
                .where(ReviewModel.product_id == product_id)
                .where(ReviewModel.status == ReviewStatus.APPROVED.value)
                .group_by(ReviewModel.rating)
            )

            result = await self.session.execute(dist_stmt)
            distribution = {rating: count for rating, count in result.all()}

            # Fill in missing ratings with 0
            rating_distribution = {i: distribution.get(i, 0) for i in range(1, 6)}

            return {
                "average_rating": float(avg_rating) if avg_rating is not None else 0.0,
                "total_reviews": total_reviews or 0,
                "rating_distribution": rating_distribution,
            }

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to get rating stats: {str(e)}")

    async def update(self, review: Review) -> Review:
        """Update an existing review"""
        try:
            if review.id is None:
                raise RepositoryError("Review ID is required for update")

            stmt = select(ReviewModel).where(ReviewModel.id == review.id)
            result = await self.session.execute(stmt)
            db_review = result.scalar_one_or_none()

            if db_review is None:
                raise RepositoryError(f"Review {review.id} not found")

            # Update fields
            db_review.rating = review.rating.value
            db_review.title = review.title
            db_review.content = review.content
            db_review.status = review.status.value
            db_review.verified_purchase = review.verified_purchase
            db_review.helpful_count = review.helpful_count
            db_review.media_urls = review.media_urls
            db_review.attributes = review.attributes

            await self.session.commit()
            await self.session.refresh(db_review)

            return self._to_domain_model(db_review)

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to update review: {str(e)}")

    async def delete(self, review_id: str) -> bool:
        """Delete a review"""
        try:
            stmt = delete(ReviewModel).where(ReviewModel.id == review_id)
            result = await self.session.execute(stmt)
            await self.session.commit()

            return result.rowcount > 0

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to delete review: {str(e)}")

    async def count_by_product(
        self, product_id: str, status: Optional[ReviewStatus] = None
    ) -> int:
        """Count reviews for a product"""
        try:
            stmt = select(func.count(ReviewModel.id)).where(
                ReviewModel.product_id == product_id
            )

            if status is not None:
                stmt = stmt.where(ReviewModel.status == status.value)

            result = await self.session.execute(stmt)
            count = result.scalar()

            return count or 0

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to count reviews: {str(e)}")

    def _to_domain_model(self, db_review: ReviewModel) -> Review:
        """Convert ORM model to domain model"""
        return Review(
            id=db_review.id,
            product_id=db_review.product_id,
            customer_id=db_review.customer_id,
            rating=ReviewRating(db_review.rating),
            title=db_review.title,
            content=db_review.content,
            status=ReviewStatus(db_review.status),
            created_at=db_review.created_at,
            updated_at=db_review.updated_at,
            verified_purchase=db_review.verified_purchase,
            helpful_count=db_review.helpful_count,
            media_urls=db_review.media_urls or [],
            attributes=db_review.attributes or {},
        )
