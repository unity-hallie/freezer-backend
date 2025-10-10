"""Add Discord integration fields to Household

Revision ID: c70775dc65a4
Revises: 936ecb15a293
Create Date: 2025-10-10 22:36:17.526228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c70775dc65a4'
down_revision: Union[str, None] = '936ecb15a293'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Discord integration fields to households table
    op.add_column('households', sa.Column('discord_guild_id', sa.String(length=50), nullable=True))
    op.add_column('households', sa.Column('discord_notification_channel_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_households_discord_guild_id'), 'households', ['discord_guild_id'], unique=False)


def downgrade() -> None:
    # Remove Discord integration fields
    op.drop_index(op.f('ix_households_discord_guild_id'), table_name='households')
    op.drop_column('households', 'discord_notification_channel_id')
    op.drop_column('households', 'discord_guild_id')
