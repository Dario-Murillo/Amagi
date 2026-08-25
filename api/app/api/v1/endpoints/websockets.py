import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.deps import DbSession, get_current_user_ws
from app.crud import crud_room
from app.services.connection_manager import manager
from app.utils.time import utcnow

# Application close code for a slug no room answers to. 1008 already means "the
# token was rejected", and the frontend has to tell the two apart.
WS_ROOM_NOT_FOUND = 4004

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{room_slug}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_slug: str,
    db: DbSession,
    token: str = Query(...),
):
    user = await get_current_user_ws(token, db)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Rooms are addressed by slug and have to exist first. Without this check any
    # string in the path spins up an ad-hoc room inside the connection registry,
    # so a typo silently becomes a private channel.
    if await crud_room.get_by_slug(db, room_slug) is None:
        await websocket.close(code=WS_ROOM_NOT_FOUND)
        return

    await manager.connect(websocket, room_slug)
    # Identity always comes from the verified token, never from the payload,
    # so a client cannot broadcast under someone else's name.
    username = user.username

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            if data.get("type") == "join":
                await manager.broadcast(
                    json.dumps(
                        {
                            "type": "join",
                            "username": username,
                            # Wire field keeps its name; the value is the slug.
                            "room_id": room_slug,
                            "timestamp": utcnow().isoformat(),
                        }
                    ),
                    room_slug,
                )
                continue

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(
                json.dumps(
                    {
                        "type": "message",
                        "username": username,
                        "message": data.get("message"),
                        "room_id": room_slug,
                        "timestamp": utcnow().isoformat(),
                    }
                ),
                room_slug,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_slug)
        await manager.broadcast(
            json.dumps(
                {
                    "event": "disconnect",
                    "username": username,
                    "room_id": room_slug,
                    "timestamp": utcnow().isoformat(),
                }
            ),
            room_slug,
        )
