"""Add merchant_id to reviews table

Revision ID: 003
Revises: 002
Create Date: 2025-11-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add merchant_id to reviews table"""
    # Add merchant_id column (nullable initially for existing data)
    op.add_column('reviews', sa.Column('merchant_id', sa.String(36), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_reviews_merchant_id',
        'reviews',
        'merchants',
        ['merchant_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create composite index for merchant_id + product_id + status (most common query)
    op.create_index(
        'idx_reviews_merchant_product_status',
        'reviews',
        ['merchant_id', 'product_id', 'status']
    )

    # Create index for merchant_id + created_at (for merchant dashboard)
    op.create_index(
        'idx_reviews_merchant_created',
        'reviews',
        ['merchant_id', 'created_at']
    )


def downgrade() -> None:
    """Remove merchant_id from reviews table"""
    op.drop_index('idx_reviews_merchant_created', 'reviews')
    op.drop_index('idx_reviews_merchant_product_status', 'reviews')
    op.drop_constraint('fk_reviews_merchant_id', 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'merchant_id')
