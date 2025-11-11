"""Create merchants table

Revision ID: 002
Revises: 001
Create Date: 2025-11-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create merchants table for multi-tenancy"""
    op.create_table(
        'merchants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False, unique=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
    )

    # Create indexes
    op.create_index('idx_merchants_email', 'merchants', ['email'])
    op.create_index('idx_merchants_api_key', 'merchants', ['api_key'])
    op.create_index('idx_merchants_active', 'merchants', ['active'])


def downgrade() -> None:
    """Drop merchants table"""
    op.drop_table('merchants')
