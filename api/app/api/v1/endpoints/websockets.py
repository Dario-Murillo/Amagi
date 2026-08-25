import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.deps import get_current_user_ws, ws_session
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
    token: str = Query(...),
):
    # The handshake is the only part of a socket's life that reads the database.
    # Declaring `DbSession` here instead would hold a pooled connection for as
    # long as the user stays connected, doing nothing.
    async with ws_session() as db:
        user = await get_current_user_ws(token, db)

        if user is None:
            # Turned away before the handshake completes, so an unauthenticated
            # peer never holds an open socket. uvicorn answers this with HTTP
            # 403 and the browser reports a plain connection failure.
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Rooms are addressed by slug and have to exist first. Without this
        # check any string in the path spins up an ad-hoc room inside the
        # connection registry, so a typo silently becomes a private channel.
        room = await crud_room.get_by_slug(db, room_slug)

        # Identity always comes from the verified token, never from the payload,
        # so a client cannot broadcast under someone else's name. Read while the
        # session is still open: afterwards the instance is detached.
        username = user.username

    if room is None:
        # Accepted first on purpose. A close code sent before the handshake
        # completes never reaches a browser -- uvicorn turns it into HTTP 403
        # and the client only ever sees 1006, indistinguishable from the server
        # being down. The token is already verified here, so opening the socket
        # just to name the reason gives nothing away.
        await websocket.accept()
        await websocket.close(code=WS_ROOM_NOT_FOUND)
        return

    await manager.connect(websocket, room_slug)

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
