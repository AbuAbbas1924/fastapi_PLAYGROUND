"""rename published_data to published_date

Revision ID: 6bb14a949625
Revises: 5b29c0315366
Create Date: 2026-02-08 21:06:21.603507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bb14a949625'
down_revision: Union[str, Sequence[str], None] = '5b29c0315366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('books', 'published_data', new_column_name='published_date')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('books', 'published_date', new_column_name='published_data')
