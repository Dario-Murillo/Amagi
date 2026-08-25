"""Rooms are read-only over the API: seeded by migration, never created here."""
import pytest


@pytest.mark.usefixtures("seeded_rooms")
async def test_list_rooms_returns_the_card_copy(client, v1, auth_header):
    response = await client.get(f"{v1}/rooms", headers=auth_header)

    assert response.status_code == 200
    body = response.json()
    assert {room["slug"] for room in body} == {"general", "tech"}

    general = next(room for room in body if room["slug"] == "general")
    assert general["name"] == "General"
    assert general["topic"] == "Chat"
    assert general["description"] == "Open conversation for everyone."


@pytest.mark.usefixtures("seeded_rooms")
async def test_list_rooms_requires_a_token(client, v1):
    response = await client.get(f"{v1}/rooms")

    assert response.status_code == 401


@pytest.mark.usefixtures("seeded_rooms")
async def test_get_room_by_slug(client, v1, auth_header):
    response = await client.get(f"{v1}/rooms/general", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["name"] == "General"


async def test_get_room_returns_404_for_an_unknown_slug(client, v1, auth_header):
    response = await client.get(f"{v1}/rooms/not-a-room", headers=auth_header)

    assert response.status_code == 404


async def test_creating_a_room_is_not_exposed(client, v1, auth_header):
    """Users have no permission to create rooms, so the verb must not exist."""
    response = await client.post(
        f"{v1}/rooms", json={"slug": "x", "name": "X"}, headers=auth_header
    )

    assert response.status_code == 405
