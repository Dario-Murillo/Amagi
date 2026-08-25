from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.crud import crud_room
from app.models.room import Room
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
