import pytest

from app.core.database import AsyncSessionLocal
from app.crud import crud_room
from app.schemas.room import RoomCreate

CREDENTIALS = {"username": "ghost_99", "password": "supersecret"}


@pytest.fixture
async def auth_header(client, v1) -> dict[str, str]:
    await client.post(f"{v1}/users/register", json=CREDENTIALS)
    token = (await client.post(f"{v1}/users/token", data=CREDENTIALS)).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seeded_room():
    """The test database is built from the metadata, not from the migrations, so
    the rooms the migration seeds have to be inserted here."""
    async with AsyncSessionLocal() as session:
        room = await crud_room.create(
            session,
            RoomCreate(
                slug="general",
                name="General",
                topic="Chat",
                description="Open conversation for everyone.",
            ),
        )
        await session.commit()
        return room


async def test_list_rooms_returns_the_card_copy(client, v1, auth_header, seeded_room):
    response = await client.get(f"{v1}/rooms", headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "general"
    assert body[0]["name"] == "General"
    assert body[0]["topic"] == "Chat"
    assert body[0]["description"] == "Open conversation for everyone."


async def test_list_rooms_requires_a_token(client, v1, seeded_room):
    response = await client.get(f"{v1}/rooms")

    assert response.status_code == 401


async def test_get_room_by_slug(client, v1, auth_header, seeded_room):
    response = await client.get(f"{v1}/rooms/general", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["name"] == "General"


async def test_get_room_returns_404_for_an_unknown_slug(client, v1, auth_header):
    response = await client.get(f"{v1}/rooms/not-a-room", headers=auth_header)

    assert response.status_code == 404


async def test_creating_a_room_is_not_exposed(client, v1, auth_header):
    """Users have no permission to create rooms, so the verb must not exist."""
    response = await client.post(f"{v1}/rooms", json={"slug": "x", "name": "X"}, headers=auth_header)

    assert response.status_code == 405
