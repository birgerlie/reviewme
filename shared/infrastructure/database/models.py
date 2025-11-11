"""
Shared Database Models
SQLAlchemy models for shared entities (merchants, review tokens)
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from shared.database import Base


class MerchantModel(Base):
    """
    Merchant database model
    Represents a merchant/store account in the system
    """
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    api_key = Column(String(255), nullable=False, unique=True, index=True)
    active = Column(Boolean, nullable=False, default=True, index=True)
    plan = Column(String(50), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    settings = Column(JSONB, nullable=False, default={})


class ReviewTokenModel(Base):
    """
    Review Token database model
    Secure tokens for review submission
    """
    __tablename__ = "review_tokens"

    id = Column(String(36), primary_key=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(255), nullable=False)
    order_id = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=True)
    used = Column(Boolean, nullable=False, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
