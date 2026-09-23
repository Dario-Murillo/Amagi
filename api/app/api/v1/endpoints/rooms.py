from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.crud import crud_message, crud_room
from app.models.room import Room
from app.schemas.message import MESSAGE_PAGE_SIZE, MessageResponse
from app.schemas.room import RoomResponse

# Read-only on purpose: rooms are seeded by migration and users have no
# permission to create or delete them, so no write endpoints are exposed.
# Listing requires a session, the same as opening a room socket does.
router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomResponse])
async def get_rooms(current_user: CurrentUser, db: DbSession) -> list[Room]:
    """Every room, in the order the room list renders them."""
    return await crud_room.get_all(db)


@router.get("/{slug}", response_model=RoomResponse)
async def get_room(slug: str, current_user: CurrentUser, db: DbSession) -> Room:
    room = await crud_room.get_by_slug(db, slug)

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    return room


@router.get("/{slug}/messages", response_model=list[MessageResponse])
async def get_room_messages(
    slug: str,
    db: DbSession,
    before: Annotated[int | None, Query(gt=0)] = None,
) -> list[MessageResponse]:
    """One page of history, oldest first: the newest page without `before`, and
    the page just older than message `before` with it. An empty page means the
    start of the room has been reached."""
    room = await crud_room.get_by_slug(db, slug)

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    rows = await crud_message.page_before(db, room.id, before, MESSAGE_PAGE_SIZE)
    return [
        MessageResponse(
            id=message.id,
            username=username,
            message=message.text,
            timestamp=message.created_at,
        )
        for message, username in rows
    ]
