"""
SQLAlchemy database models
These are ORM models, separate from domain models
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class ReviewModel(Base):
    """
    SQLAlchemy model for reviews table

    Indexes:
    - idx_reviews_product_status: For filtering by product and status (most common query)
    - idx_reviews_created_at: For sorting by date
    - idx_reviews_rating: For rating calculations
    - idx_reviews_customer: For finding customer's reviews
    """

    __tablename__ = "reviews"

    # Primary key
    id = Column(
        String(36), primary_key=True, default=lambda: f"rev_{uuid.uuid4().hex[:24]}"
    )

    # Foreign keys (as strings since we don't have product/customer tables yet)
    product_id = Column(String(255), nullable=False)
    customer_id = Column(String(255), nullable=False)

    # Review content
    rating = Column(Integer, CheckConstraint("rating >= 1 AND rating <= 5"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(String, nullable=False)

    # Status tracking
    status = Column(String(50), nullable=False, default="pending")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Additional fields
    verified_purchase = Column(Boolean, default=False, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)

    # JSONB columns for flexible data
    media_urls = Column(JSONB, default=list, nullable=False)
    attributes = Column(JSONB, default=dict, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_reviews_product_status", "product_id", "status"),
        Index("idx_reviews_created_at", "created_at"),
        Index("idx_reviews_rating", "rating"),
        Index("idx_reviews_customer", "customer_id"),
        Index("idx_reviews_verified", "verified_purchase"),
    )

    def __repr__(self) -> str:
        return f"<ReviewModel(id={self.id}, product_id={self.product_id}, rating={self.rating})>"
