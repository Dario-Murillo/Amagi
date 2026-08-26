import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """In-memory registry of the sockets connected to each room.

    Single-process only: a second worker would keep its own dict and rooms would
    silently split. Replacing this with Redis Pub/Sub is a planned milestone.
    """

    def __init__(self):
        self._active_connections: dict[str, list[WebSocket]] = {}

    async def connect(
        self, websocket: WebSocket, room_slug: str, subprotocol: str | None = None
    ):
        # The subprotocol has to be echoed back or the browser rejects the
        # handshake; it is how the token reached us in the first place.
        await websocket.accept(subprotocol=subprotocol)
        if room_slug not in self._active_connections:
            self._active_connections[room_slug] = []
        self._active_connections[room_slug].append(websocket)

    def disconnect(self, websocket: WebSocket, room_slug: str):
        """Unregister a socket. Safe to call for a socket or a room that is
        already gone: a broadcast drops dead sockets on its own, so the handler
        that owns one routinely asks for a removal that already happened."""
        connections = self._active_connections.get(room_slug)

        if connections is None:
            return

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            del self._active_connections[room_slug]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, room_slug: str):
        # Iterate a copy: a failing socket is unregistered below, and the list
        # must not change underneath the loop.
        for connection in list(self._active_connections.get(room_slug, [])):
            try:
                await connection.send_text(message)
            except Exception:
                # One dead socket must not swallow the message for the rest of
                # the room. Drop it here rather than waiting for its own handler
                # to notice, which it may never get the chance to do.
                logger.warning("dropping a dead socket from room %s", room_slug)
                self.disconnect(connection, room_slug)


manager = ConnectionManager()
