"""add room slug and seed default rooms

Revision ID: a3f1c9d24b70
Revises: e15e0ef1aba5
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f1c9d24b70'
down_revision: Union[str, Sequence[str], None] = 'e15e0ef1aba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The rooms the frontend has been addressing all along, so a fresh database
# answers the slugs in `web/lib/rooms.ts` instead of rejecting every socket.
DEFAULT_ROOMS = [
    ("general", "General"),
    ("tech", "Tech"),
    ("random", "Random"),
    ("ideas", "Ideas"),
    ("help", "Help"),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("rooms", sa.Column("slug", sa.String(), nullable=True))

    # Rows created before this column exists still have to satisfy the NOT NULL
    # below, so derive a slug from the display name they already carry.
    op.execute(
        "UPDATE rooms SET slug = lower(replace(name, ' ', '-')) WHERE slug IS NULL"
    )

    # ON CONFLICT keeps this idempotent against a database that was seeded by
    # hand: an existing room keeps the slug the UPDATE above gave it.
    values = ", ".join(f"('{slug}', '{name}', now())" for slug, name in DEFAULT_ROOMS)
    op.execute(
        f"INSERT INTO rooms (slug, name, created_at) VALUES {values} "
        "ON CONFLICT (name) DO NOTHING"
    )

    op.alter_column("rooms", "slug", existing_type=sa.String(), nullable=False)
    op.create_unique_constraint("uq_rooms_slug", "rooms", ["slug"])


def downgrade() -> None:
    """Downgrade schema."""
    # The seeded rows are left in place: they are indistinguishable from rooms
    # created afterwards, and dropping them would take real data with them.
    op.drop_constraint("uq_rooms_slug", "rooms", type_="unique")
    op.drop_column("rooms", "slug")
