"""add calculated member age

Revision ID: a98cbb942e0b
Revises: 6dee8a2ebd0c
Create Date: 2026-07-02 21:11:05.572544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a98cbb942e0b'
down_revision: Union[str, Sequence[str], None] = '6dee8a2ebd0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('members', sa.Column('age', sa.Integer(), nullable=True))
    op.execute(
        """
        update members
        set age = extract(year from age(current_date, birth_date))::int
        """
    )
    op.alter_column('members', 'age', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('members', 'age')
