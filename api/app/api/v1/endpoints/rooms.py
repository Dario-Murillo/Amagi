from fastapi import APIRouter

# NOTE: these handlers are still stubs. `app.crud.crud_room` already holds the
# queries they need, but wiring them up is blocked on deciding whether a room is
# addressed by its integer id or by a unique slug -- the frontend and the
# WebSocket route currently use string slugs ("general", "tech") while
# `rooms.id` is an integer.
router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/")
async def get_rooms():
    return []


@router.post("/")
async def create_room(name: str):
    pass


@router.get("/{room_id}")
async def get_room(room_id: str):
    return None


@router.delete("/{room_id}")
async def delete_room(room_id: str):
    return None
