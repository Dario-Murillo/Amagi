import pytest

from app.services.connection_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent: list[str] = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        self.sent.append(message)


@pytest.fixture
def manager() -> ConnectionManager:
    return ConnectionManager()


async def test_connect_accepts_and_registers_the_socket(manager):
    socket = FakeWebSocket()

    await manager.connect(socket, "general")

    assert socket.accepted
    await manager.broadcast("hello", "general")
    assert socket.sent == ["hello"]


async def test_broadcast_only_reaches_the_matching_room(manager):
    here, elsewhere = FakeWebSocket(), FakeWebSocket()
    await manager.connect(here, "general")
    await manager.connect(elsewhere, "tech")

    await manager.broadcast("hello", "general")

    assert here.sent == ["hello"]
    assert elsewhere.sent == []


async def test_disconnect_stops_delivery(manager):
    socket = FakeWebSocket()
    await manager.connect(socket, "general")

    manager.disconnect(socket, "general")
    await manager.broadcast("hello", "general")

    assert socket.sent == []
