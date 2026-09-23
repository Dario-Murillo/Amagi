"""index messages by room

Revision ID: d8b3e6f14a27
Revises: c4a91f83d2e6
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8b3e6f14a27'
down_revision: Union[str, Sequence[str], None] = 'c4a91f83d2e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Every history page is "this room, ids below N, newest first": this index
    # answers it with a range scan instead of sorting the whole table.
    op.create_index("ix_messages_room_id_id", "messages", ["room_id", "id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_messages_room_id_id", table_name="messages")
