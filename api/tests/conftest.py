import os
import tempfile
from pathlib import Path

# Settings are validated at import time, so the test environment has to be in
# place before anything under `app.` is imported. Env vars win over `.env`.
_TEST_DB = Path(tempfile.gettempdir()) / "amagi_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from httpx_ws.transport import ASGIWebSocketTransport  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import AsyncSessionLocal, Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.room import Room  # noqa: E402

# The production schema is owned by Alembic, but its migrations carry
# Postgres-specific types, so the throwaway SQLite test database is built
# straight from the metadata instead.


@pytest.fixture(autouse=True)
async def db_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def ws_client():
    """Builds clients that speak WebSocket to the ASGI app in-process.

    A plain `ASGITransport` only carries HTTP, so the socket routes need their
    own transport. This hands back a factory rather than an open client on
    purpose: the transport holds an anyio cancel scope that has to be entered
    and left by the same task, and pytest-asyncio runs fixture setup and
    teardown in different ones. The caller opens it inside its own test.
    """

    def _client() -> AsyncClient:
        return AsyncClient(
            transport=ASGIWebSocketTransport(app), base_url="http://test"
        )

    return _client


@pytest.fixture
def v1() -> str:
    return settings.api_v1_prefix


@pytest.fixture
async def seeded_rooms():
    """The test database is built from the metadata, not from the migrations, so
    the rooms the migration seeds have to be inserted here."""
    async with AsyncSessionLocal() as session:
        session.add(
            Room(
                slug="general",
                name="General",
                topic="Chat",
                description="Open conversation for everyone.",
            )
        )
        session.add(Room(slug="tech", name="Tech", topic="Dev", description="Code."))
        await session.commit()


@pytest.fixture
def make_token(client, v1):
    """Registers a user and returns their access token."""

    async def _make(username: str = "ghost_99") -> str:
        credentials = {"username": username, "password": "supersecret"}
        await client.post(f"{v1}/users/register", json=credentials)
        response = await client.post(f"{v1}/users/token", data=credentials)
        return response.json()["access_token"]

    return _make


@pytest.fixture
async def token(make_token) -> str:
    return await make_token()


@pytest.fixture
async def auth_header(token) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
