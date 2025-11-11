"""
Platform Service Database Models
SQLAlchemy models for platform-specific entities
"""
from sqlalchemy import Column, String, Boolean, Text, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from shared.database import Base


class PlatformMerchantModel(Base):
    """
    Platform Merchant database model
    OAuth-connected merchants from e-commerce platforms
    """
    __tablename__ = "platform_merchants"

    id = Column(String(36), primary_key=True)
    platform = Column(String(50), nullable=False, index=True)
    platform_domain = Column(String(255), nullable=False)
    platform_merchant_id = Column(String(255), nullable=False)

    # OAuth
    access_token = Column(Text, nullable=False)
    scopes = Column(ARRAY(String), nullable=False, default=[])
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Store info
    store_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    currency = Column(String(10), nullable=False, default="USD")
    timezone = Column(String(50), nullable=False, default="UTC")

    # Status
    installed_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=True, index=True)

    # Configuration
    widget_config = Column(JSONB, nullable=False, default={})
    platform_metadata = Column(JSONB, nullable=False, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
