"""create group participations table

Revision ID: 4741fbb74617
Revises: 4d9cfbafe5db
Create Date: 2026-07-02 21:23:51.564279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4741fbb74617'
down_revision: Union[str, Sequence[str], None] = '4d9cfbafe5db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'group_participations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_group_participations_active_member_group',
        'group_participations',
        ['member_id', 'group_id'],
        unique=True,
        postgresql_where=sa.text('active = true'),
    )
    op.create_index(
        op.f('ix_group_participations_group_id'),
        'group_participations',
        ['group_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_group_participations_member_id'),
        'group_participations',
        ['member_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_group_participations_member_id'), table_name='group_participations')
    op.drop_index(op.f('ix_group_participations_group_id'), table_name='group_participations')
    op.drop_index('ix_group_participations_active_member_group', table_name='group_participations')
    op.drop_table('group_participations')
