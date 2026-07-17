"""create attendances table

Revision ID: 6b65e5872460
Revises: 2503ed71acc8
Create Date: 2026-07-02 22:33:43.148053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6b65e5872460'
down_revision: Union[str, Sequence[str], None] = '2503ed71acc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'attendances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('checked_in_at', sa.DateTime(), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'member_id', name='uq_attendances_event_member'),
    )
    op.create_index(op.f('ix_attendances_event_id'), 'attendances', ['event_id'], unique=False)
    op.create_index(op.f('ix_attendances_member_id'), 'attendances', ['member_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_attendances_member_id'), table_name='attendances')
    op.drop_index(op.f('ix_attendances_event_id'), table_name='attendances')
    op.drop_table('attendances')
