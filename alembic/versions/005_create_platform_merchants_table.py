"""Create platform_merchants table

Revision ID: 005
Revises: 004
Create Date: 2025-11-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create platform_merchants table for OAuth-connected merchants"""
    op.create_table(
        'platform_merchants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('platform_domain', sa.String(255), nullable=False),
        sa.Column('platform_merchant_id', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('store_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='USD'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('widget_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('platform_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create unique constraint on platform + domain
    op.create_unique_constraint(
        'uq_platform_merchants_platform_domain',
        'platform_merchants',
        ['platform', 'platform_domain']
    )

    # Create indexes
    op.create_index('idx_platform_merchants_platform_domain', 'platform_merchants', ['platform', 'platform_domain'])
    op.create_index('idx_platform_merchants_email', 'platform_merchants', ['email'])
    op.create_index('idx_platform_merchants_active', 'platform_merchants', ['active'])


def downgrade() -> None:
    """Drop platform_merchants table"""
    op.drop_table('platform_merchants')
