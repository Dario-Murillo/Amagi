from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.utils.time import utcnow


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # URL-safe identifier: it is what the WebSocket path and the frontend
    # address a room by. `name` stays purely for display, so renaming a room
    # never breaks the links pointing at it.
    slug: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    # Card copy for the room list. It lives here rather than in the frontend so
    # the client renders whatever rooms the database actually holds.
    topic: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
