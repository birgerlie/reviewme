"""Create reviews table

Revision ID: 001
Revises:
Create Date: 2025-01-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reviews table with all indexes"""
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(255), nullable=False),
        sa.Column('customer_id', sa.String(255), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('verified_purchase', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('media_urls', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('attributes', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    # Create indexes for performance
    op.create_index('idx_reviews_product_status', 'reviews', ['product_id', 'status'])
    op.create_index('idx_reviews_created_at', 'reviews', ['created_at'])
    op.create_index('idx_reviews_rating', 'reviews', ['rating'])
    op.create_index('idx_reviews_customer', 'reviews', ['customer_id'])
    op.create_index('idx_reviews_verified', 'reviews', ['verified_purchase'])


def downgrade() -> None:
    """Drop reviews table"""
    op.drop_table('reviews')
