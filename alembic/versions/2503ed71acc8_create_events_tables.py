"""create events tables

Revision ID: 2503ed71acc8
Revises: 4741fbb74617
Create Date: 2026-07-02 22:26:40.532311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2503ed71acc8'
down_revision: Union[str, Sequence[str], None] = '4741fbb74617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    event_status = postgresql.ENUM(
        'SCHEDULED',
        'IN_PROGRESS',
        'COMPLETED',
        'CANCELLED',
        'PENDING_REGISTRATION',
        name='eventstatus',
        create_type=False,
    )
    weekday = postgresql.ENUM(
        'MONDAY',
        'TUESDAY',
        'WEDNESDAY',
        'THURSDAY',
        'FRIDAY',
        'SATURDAY',
        'SUNDAY',
        name='weekday',
        create_type=False,
    )

    event_status.create(op.get_bind(), checkfirst=True)
    weekday.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('recurring', sa.Boolean(), nullable=False),
        sa.Column('weekdays', postgresql.ARRAY(weekday), nullable=False),
        sa.Column('status', event_status, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_events_name'), 'events', ['name'], unique=False)

    op.create_table(
        'event_groups',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id', 'group_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('event_groups')
    op.drop_index(op.f('ix_events_name'), table_name='events')
    op.drop_table('events')

    postgresql.ENUM(name='weekday').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='eventstatus').drop(op.get_bind(), checkfirst=True)
