from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.user import User


async def create(db: AsyncSession, *, text: str, user_id: int, room_id: int) -> Message:
    message = Message(text=text, user_id=user_id, room_id=room_id)
    db.add(message)
    await db.flush()
    return message


async def page_before(
    db: AsyncSession, room_id: int, before: int | None, limit: int
) -> list[tuple[Message, str]]:
    """Up to `limit` messages older than `before` (the newest when None), oldest
    first, each with its author's username.

    Keyset on `id` rather than an offset: a page stays exact while new messages
    keep arriving, where an offset would shift under them and repeat rows.
    """
    query = (
        select(Message, User.username)
        .join(User, User.id == Message.user_id)
        .where(Message.room_id == room_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    if before is not None:
        query = query.where(Message.id < before)

    rows = (await db.execute(query)).all()
    return [(message, username) for message, username in reversed(rows)]
