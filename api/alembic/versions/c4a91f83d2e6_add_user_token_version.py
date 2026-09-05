"""add user token version

Revision ID: c4a91f83d2e6
Revises: b7e2d5a81c93
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4a91f83d2e6'
down_revision: Union[str, Sequence[str], None] = 'b7e2d5a81c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The server default is what gives existing rows a value, and it is kept so
    # a row inserted outside the ORM still gets one.
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "token_version")
