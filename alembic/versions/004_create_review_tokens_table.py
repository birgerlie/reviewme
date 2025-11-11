"""Create review_tokens table

Revision ID: 004
Revises: 003
Create Date: 2025-11-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create review_tokens table for secure review submission"""
    op.create_table(
        'review_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('merchant_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(255), nullable=False),
        sa.Column('order_id', sa.String(255), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Add foreign key to merchants
    op.create_foreign_key(
        'fk_review_tokens_merchant_id',
        'review_tokens',
        'merchants',
        ['merchant_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create indexes for performance
    op.create_index('idx_review_tokens_token', 'review_tokens', ['token'])
    op.create_index(
        'idx_review_tokens_unused',
        'review_tokens',
        ['used', 'expires_at'],
        postgresql_where=sa.text('used = false')
    )
    op.create_index(
        'idx_review_tokens_merchant_product',
        'review_tokens',
        ['merchant_id', 'product_id']
    )
    op.create_index(
        'idx_review_tokens_customer',
        'review_tokens',
        ['customer_email', 'merchant_id']
    )


def downgrade() -> None:
    """Drop review_tokens table"""
    op.drop_table('review_tokens')
