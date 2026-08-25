from fastapi import APIRouter

# NOTE: these handlers are still stubs. Rooms are addressed by their `slug`
# everywhere outside the database now, so `crud_room.get_by_slug` is the query
# these need; `rooms.id` stays an internal key for the foreign keys only.
# Wiring them up is its own change: they also need `CurrentUser`, since create
# and delete are currently unauthenticated.
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
