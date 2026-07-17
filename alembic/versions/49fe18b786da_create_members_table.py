"""create members table

Revision ID: 49fe18b786da
Revises: 
Create Date: 2026-07-02 20:22:01.393814

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '49fe18b786da'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    member_category = postgresql.ENUM(
        'PASTOR',
        'MEMBER',
        'VISITOR',
        'DEACON',
        'CONGREGANT',
        name='membercategory',
        create_type=False,
    )
    member_status = postgresql.ENUM('ACTIVE', 'INACTIVE', name='memberstatus', create_type=False)

    member_category.create(op.get_bind(), checkfirst=True)
    member_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('tax_id', sa.String(length=30), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('category', member_category, nullable=False),
        sa.Column('status', member_status, nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('tax_id'),
    )
    op.create_index(op.f('ix_members_email'), 'members', ['email'], unique=False)
    op.create_index(op.f('ix_members_tax_id'), 'members', ['tax_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_members_tax_id'), table_name='members')
    op.drop_index(op.f('ix_members_email'), table_name='members')
    op.drop_table('members')

    postgresql.ENUM(name='memberstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='membercategory').drop(op.get_bind(), checkfirst=True)
