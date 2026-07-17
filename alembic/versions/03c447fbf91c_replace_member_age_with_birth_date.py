"""replace member age with birth date

Revision ID: 03c447fbf91c
Revises: 49fe18b786da
Create Date: 2026-07-02 21:06:45.797430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03c447fbf91c'
down_revision: Union[str, Sequence[str], None] = '49fe18b786da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'members',
        sa.Column('birth_date', sa.Date(), nullable=False, server_default='1900-01-01'),
    )
    op.alter_column('members', 'birth_date', server_default=None)
    op.drop_column('members', 'age')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'members',
        sa.Column('age', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('members', 'age', server_default=None)
    op.drop_column('members', 'birth_date')
