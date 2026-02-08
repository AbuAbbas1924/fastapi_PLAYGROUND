"""fix book modul

Revision ID: 5b29c0315366
Revises: a8dde4eaf35a
Create Date: 2026-02-08 21:05:16.125424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b29c0315366'
down_revision: Union[str, Sequence[str], None] = 'a8dde4eaf35a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
