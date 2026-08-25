import pytest

from app.core.database import AsyncSessionLocal
from app.crud import crud_room
from app.schemas.room import RoomCreate


@pytest.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session


async def test_get_by_slug_finds_the_room(db):
    await crud_room.create(db, RoomCreate(slug="general", name="General"))

    room = await crud_room.get_by_slug(db, "general")

    assert room is not None
    assert room.name == "General"


async def test_get_by_slug_returns_none_for_an_unknown_slug(db):
    """The WebSocket handler closes the socket on this None, which is what keeps
    an arbitrary path from spinning up an ad-hoc room."""
    assert await crud_room.get_by_slug(db, "not-a-room") is None


async def test_slug_rejects_characters_that_would_need_escaping():
    with pytest.raises(ValueError):
        RoomCreate(slug="Not A Slug!", name="Nope")
