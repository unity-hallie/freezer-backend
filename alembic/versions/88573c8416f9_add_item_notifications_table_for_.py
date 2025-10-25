"""Add item_notifications table for tracking notification state

Revision ID: 88573c8416f9
Revises: c70775dc65a4
Create Date: 2025-10-25 11:24:20.375041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88573c8416f9'
down_revision: Union[str, None] = 'c70775dc65a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'item_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_item_notifications_item_id', 'item_id'),
        sa.Index('ix_item_notifications_household_id', 'household_id')
    )


def downgrade() -> None:
    op.drop_table('item_notifications')
