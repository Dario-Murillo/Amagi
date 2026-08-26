import pytest

from app.services.connection_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent: list[str] = []

    async def accept(self, subprotocol: str | None = None):
        self.accepted = True
        self.subprotocol = subprotocol

    async def send_text(self, message: str):
        self.sent.append(message)


class DeadWebSocket(FakeWebSocket):
    """Stands in for a socket the peer has already dropped."""

    async def send_text(self, message: str):
        raise RuntimeError("Cannot call 'send' once a close message has been sent.")


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


async def test_a_dead_socket_does_not_stop_the_rest_of_the_room(manager):
    """One unreachable peer used to raise mid-loop, and every socket after it in
    the list silently missed the message."""
    dead, alive = DeadWebSocket(), FakeWebSocket()
    await manager.connect(dead, "general")
    await manager.connect(alive, "general")

    await manager.broadcast("hello", "general")

    assert alive.sent == ["hello"]


async def test_a_dead_socket_is_dropped_from_the_room(manager):
    dead, alive = DeadWebSocket(), FakeWebSocket()
    await manager.connect(dead, "general")
    await manager.connect(alive, "general")

    await manager.broadcast("first", "general")
    await manager.broadcast("second", "general")

    # The second broadcast no longer attempts the dead socket at all.
    assert alive.sent == ["first", "second"]


async def test_disconnecting_twice_is_harmless(manager):
    """A broadcast drops dead sockets itself, so the handler that owns one
    routinely asks for a removal that already happened."""
    socket = FakeWebSocket()
    await manager.connect(socket, "general")

    manager.disconnect(socket, "general")
    manager.disconnect(socket, "general")


async def test_disconnecting_from_an_unknown_room_is_harmless(manager):
    manager.disconnect(FakeWebSocket(), "never-existed")
