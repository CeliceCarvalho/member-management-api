"""create groups table

Revision ID: 4d9cfbafe5db
Revises: a98cbb942e0b
Create Date: 2026-07-02 21:14:16.338219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4d9cfbafe5db'
down_revision: Union[str, Sequence[str], None] = 'a98cbb942e0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    group_type = postgresql.ENUM(
        'CELL',
        'MINISTRY',
        'DEPARTMENT',
        'EBD_CLASS',
        name='grouptype',
        create_type=False,
    )
    group_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('type', group_type, nullable=False),
        sa.Column('weekday', sa.String(length=20), nullable=True),
        sa.Column('time', sa.Time(), nullable=True),
        sa.Column('recurring_location', sa.String(length=200), nullable=True),
        sa.Column('leader_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('co_leader_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['co_leader_id'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['leader_id'], ['members.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_groups_name'), 'groups', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_groups_name'), table_name='groups')
    op.drop_table('groups')
    postgresql.ENUM(name='grouptype').drop(op.get_bind(), checkfirst=True)
