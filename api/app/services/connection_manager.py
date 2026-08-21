from fastapi import WebSocket


class ConnectionManager:
    """In-memory registry of the sockets connected to each room.

    Single-process only: a second worker would keep its own dict and rooms would
    silently split. Replacing this with Redis Pub/Sub is a planned milestone.
    """

    def __init__(self):
        self._active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self._active_connections:
            self._active_connections[room_id] = []
        self._active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        self._active_connections[room_id].remove(websocket)

        if not self._active_connections[room_id]:
            del self._active_connections[room_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, room_id: str):
        connections = self._active_connections.get(room_id, [])
        for connection in connections:
            await connection.send_text(message)


manager = ConnectionManager()
