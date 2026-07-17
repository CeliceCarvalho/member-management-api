"""add member photo url

Revision ID: 6dee8a2ebd0c
Revises: 03c447fbf91c
Create Date: 2026-07-02 21:09:02.759865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dee8a2ebd0c'
down_revision: Union[str, Sequence[str], None] = '03c447fbf91c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('members', sa.Column('photo_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('members', 'photo_url')
