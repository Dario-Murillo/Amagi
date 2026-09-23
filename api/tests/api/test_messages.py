"""Messages outlive the socket: saved on send, served back as history."""
import json

import pytest
from httpx_ws import aconnect_ws

from app.api.v1.endpoints.websockets import WS_BEARER_SUBPROTOCOL
from app.core.database import AsyncSessionLocal
from app.crud import crud_message, crud_room
from app.schemas.message import MESSAGE_PAGE_SIZE

pytestmark = pytest.mark.usefixtures("seeded_rooms")


async def send(ws_client, token: str, *texts: str) -> list[dict]:
    """Sends each text over a real socket and returns the broadcasts."""
    frames = []
    async with ws_client() as client:
        async with aconnect_ws(
            "http://test/api/v1/ws/general",
            client,
            subprotocols=[WS_BEARER_SUBPROTOCOL, token],
        ) as ws:
            for text in texts:
                await ws.send_text(json.dumps({"type": "message", "message": text}))
                frames.append(json.loads(await ws.receive_text(timeout=2)))
    return frames


async def history(client, v1, token, **params):
    return await client.get(
        f"{v1}/rooms/general/messages",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
    )


async def test_a_sent_message_is_stored_and_served_back(client, v1, ws_client, token):
    [frame] = await send(ws_client, token, "hola")

    response = await history(client, v1, token)

    assert response.status_code == 200
    [stored] = response.json()
    assert stored["id"] == frame["id"]
    assert stored["username"] == "ghost_99"
    assert stored["message"] == "hola"


async def test_the_live_frame_and_history_agree_on_the_row(client, v1, ws_client, token):
    """Same id, same text, same timestamp: that is what lets the client merge a
    history page with frames it already has without showing anything twice."""
    frames = await send(ws_client, token, "uno", "dos")

    stored = (await history(client, v1, token)).json()

    assert [m["id"] for m in stored] == [f["id"] for f in frames]
    assert [m["message"] for m in stored] == ["uno", "dos"]


async def seed(count: int) -> list[int]:
    async with AsyncSessionLocal() as db:
        room = await crud_room.get_by_slug(db, "general")
        ids = [
            (await crud_message.create(db, text=f"m{n}", user_id=1, room_id=room.id)).id
            for n in range(count)
        ]
        await db.commit()
    return ids


async def test_history_pages_backwards_without_gaps_or_repeats(client, v1, token):
    ids = await seed(MESSAGE_PAGE_SIZE + 30)

    newest = (await history(client, v1, token)).json()
    older = (await history(client, v1, token, before=newest[0]["id"])).json()
    end = (await history(client, v1, token, before=older[0]["id"])).json()

    assert [m["id"] for m in newest] == ids[-MESSAGE_PAGE_SIZE:]
    assert [m["id"] for m in older] == ids[:30]
    assert end == []


async def test_history_requires_a_token(client, v1):
    assert (await client.get(f"{v1}/rooms/general/messages")).status_code == 401


async def test_history_of_an_unknown_room_is_404(client, v1, token):
    response = await client.get(
        f"{v1}/rooms/not-a-room/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
