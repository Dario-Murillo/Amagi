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

from app.core.config import settings  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

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
def v1() -> str:
    return settings.api_v1_prefix
