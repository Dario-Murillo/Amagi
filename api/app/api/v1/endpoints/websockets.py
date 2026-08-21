import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.deps import DbSession, get_current_user_ws
from app.services.connection_manager import manager
from app.utils.time import utcnow

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    db: DbSession,
    token: str = Query(...),
):
    user = await get_current_user_ws(token, db)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id)
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
                            "room_id": room_id,
                            "timestamp": utcnow().isoformat(),
                        }
                    ),
                    room_id,
                )
                continue

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(
                json.dumps(
                    {
                        "type": "message",
                        "username": username,
                        "message": data.get("message"),
                        "room_id": room_id,
                        "timestamp": utcnow().isoformat(),
                    }
                ),
                room_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(
            json.dumps(
                {
                    "event": "disconnect",
                    "username": username,
                    "room_id": room_id,
                    "timestamp": utcnow().isoformat(),
                }
            ),
            room_id,
        )
