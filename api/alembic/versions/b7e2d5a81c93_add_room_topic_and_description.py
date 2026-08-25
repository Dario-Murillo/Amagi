"""add room topic and description

Revision ID: b7e2d5a81c93
Revises: a3f1c9d24b70
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7e2d5a81c93'
down_revision: Union[str, Sequence[str], None] = 'a3f1c9d24b70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The copy the room cards used to carry hardcoded in `web/lib/rooms.ts`. Moving
# it here is what lets the frontend drop its fixed list and render whatever the
# database actually holds.
DEFAULT_ROOM_CONTENT = [
    ("general", "Chat", "Open conversation for everyone."),
    ("tech", "Dev", "Programming, tools, and everything code."),
    ("random", "Off-topic", "Anything goes. No rules here."),
    ("ideas", "Product", "Share what you're building or thinking about."),
    ("help", "Support", "Ask questions, get unstuck."),
]


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("rooms", sa.Column("topic", sa.String(), nullable=True))
    op.add_column("rooms", sa.Column("description", sa.String(), nullable=True))

    # The five default rooms already exist from the previous revision, so this
    # fills them in rather than inserting them again.
    for slug, topic, description in DEFAULT_ROOM_CONTENT:
        op.execute(
            f"UPDATE rooms SET topic = {_quote(topic)}, "
            f"description = {_quote(description)} WHERE slug = {_quote(slug)}"
        )

    # Any other room predates these columns and has nothing to say yet; an empty
    # string keeps the NOT NULL below honest without inventing copy for it.
    op.execute("UPDATE rooms SET topic = '' WHERE topic IS NULL")
    op.execute("UPDATE rooms SET description = '' WHERE description IS NULL")

    op.alter_column("rooms", "topic", existing_type=sa.String(), nullable=False)
    op.alter_column("rooms", "description", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rooms", "description")
    op.drop_column("rooms", "topic")
