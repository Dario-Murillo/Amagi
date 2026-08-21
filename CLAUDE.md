# Amagi — Claude Context File

Real-time multi-room chat application. Python/FastAPI backend, vanilla JS + Alpine.js frontend. No frontend framework, no ORM magic — raw async SQLAlchemy against PostgreSQL.

## Project Structure

The backend follows a layered FastAPI layout rooted at `api/`. The frontend is a static sibling in `web/`, served independently.

```
Amagi/
├── CLAUDE.md
├── README.md
├── LICENSE
├── .gitignore
├── api/                          # FastAPI project root
│   ├── .env                      # Local environment variables (never committed)
│   ├── .env.example
│   ├── pyproject.toml            # Dependencies and package metadata
│   ├── Dockerfile
│   ├── docker-compose.yml        # Postgres + API for local orchestration
│   ├── alembic.ini
│   ├── alembic/                  # Migration scripts
│   │   ├── env.py                # Async-compatible Alembic config
│   │   └── versions/
│   ├── app/                      # Main application package
│   │   ├── main.py               # FastAPI init, CORS, lifespan, router mount
│   │   ├── api/                  # API layer (requests/responses)
│   │   │   ├── deps.py           # get_db, get_current_user, get_current_user_ws
│   │   │   └── v1/
│   │   │       ├── api.py        # Combines all v1 routers
│   │   │       └── endpoints/
│   │   │           ├── users.py       # register, token, me
│   │   │           ├── rooms.py       # stubs, pending DB wiring
│   │   │           └── websockets.py  # WebSocket route handler
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic Settings from .env
│   │   │   ├── database.py       # Engine, AsyncSessionLocal, Base
│   │   │   └── security.py       # Password hashing, JWT create/verify
│   │   ├── crud/                 # Reusable DB operations
│   │   │   ├── crud_user.py
│   │   │   └── crud_room.py
│   │   ├── models/               # SQLAlchemy ORM models, one per table
│   │   │   ├── user.py
│   │   │   ├── room.py
│   │   │   ├── room_member.py
│   │   │   └── message.py
│   │   ├── schemas/              # Pydantic validation schemas
│   │   │   ├── user.py
│   │   │   ├── room.py
│   │   │   ├── message.py
│   │   │   └── token.py
│   │   ├── services/             # Business logic and stateful integrations
│   │   │   └── connection_manager.py  # In-memory WebSocket registry
│   │   └── utils/
│   │       └── time.py           # utcnow() — default for every created_at
│   └── tests/
│       ├── conftest.py           # Test DB + AsyncClient fixtures
│       ├── api/                  # Endpoint integration tests
│       └── services/             # Unit tests for business logic
└── web/
    ├── index.html                # Single page, three screens via Alpine.js
    ├── style.css
    └── app.js                    # Alpine app() component — all state and logic
```

**Layering rule:** endpoints validate and delegate; they never build queries. Database access lives in `crud/`, stateful logic in `services/`, and anything an endpoint needs injected comes from `api/deps.py`.

## Running the Project

**Backend:**
```bash
cd api
python -m venv .venv
.venv\Scripts\Activate.ps1        # PowerShell
pip install -e ".[dev]"
uvicorn app.main:app --reload
# runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd web
python -m http.server 3000 --bind 127.0.0.1
# open http://127.0.0.1:3000
```

**Tests:**
```bash
cd api
pytest
```

**Database migrations** — run from `api/`, since `alembic.ini` sets `prepend_sys_path = .` so the `app` package resolves:
```bash
cd api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

**Docker:**
```bash
cd api
docker compose up --build     # brings up Postgres + the API on :8000
```

## Environment Variables

File: `api/.env`

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/amagi
SECRET_KEY=your-secret-key-here
```

`app/core/config.py` loads these via Pydantic Settings. `DATABASE_URL` must use the `postgresql+asyncpg://` driver prefix for async SQLAlchemy to work. Settings are validated at import time, so a missing variable fails the process at startup rather than at first request.

Allowed CORS origins live in `settings.cors_origins` and default to port 3000 on `localhost`, `127.0.0.1`, and `[::1]`. The browser matches origins exactly, so the host used to open the frontend must be one of them.

## API Versioning

Every route is mounted under `settings.api_v1_prefix` (`/api/v1`), including the WebSocket endpoint. The `API` and `WS` constants in `web/app.js` already include the prefix.

## Auth Flow

- Passwords hashed with **Argon2** via `pwdlib`
- Tokens are **JWT** signed with `SECRET_KEY`, containing `sub` (user ID) and `exp`
- REST endpoints use the `CurrentUser` annotated dependency from `app/api/deps.py`, which reads from the `Authorization: Bearer` header via `oauth2_scheme`
- WebSocket endpoints can't use the Authorization header — token is passed as a query param `?token=...` and verified via `get_current_user_ws(token, db)`
- Token expiry is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30)

## WebSocket Protocol

**Connection URL:** `ws://localhost:8000/api/v1/ws/{room_id}?token={jwt}`

**Client → Server messages (JSON):**
```json
{ "type": "join", "username": "ghost_99" }
{ "type": "message", "message": "hello", "room_id": "general" }
```

**Server → Client broadcasts (JSON):**
```json
{ "type": "join", "username": "ghost_99", "room_id": "general", "timestamp": "..." }
{ "type": "message", "username": "ghost_99", "message": "hello", "room_id": "general", "timestamp": "..." }
{ "event": "disconnect", "username": "ghost_99", "room_id": "general", "timestamp": "..." }
```

Username in all server messages comes from the verified JWT, not from client payload — clients cannot spoof identity.

## Database Schema

```
users         → id, username (unique), hashed_password, created_at
rooms         → id, name (unique), created_at
room_members  → user_id (FK), room_id (FK) — composite PK
messages      → id, text, created_at, user_id (FK), room_id (FK)
```

## Key Architectural Decisions

**Async throughout** — `create_async_engine` + `asyncpg` driver. Never use `psycopg2` or sync SQLAlchemy here, it blocks the event loop.

**The request transaction belongs to `get_db`** — CRUD functions call `flush()` to obtain generated ids but never `commit()`. The `get_db` dependency commits once when the request succeeds and rolls back on any exception.

**Alembic owns schema** — never use `Base.metadata.create_all()` alongside Alembic in application code. Migrations are run manually before starting the server. The test suite is the one exception: it builds a throwaway SQLite database straight from the metadata, because the migrations carry Postgres-specific types.

**ConnectionManager is in-memory** — works for a single process. Horizontal scaling requires replacing it with Redis Pub/Sub (planned milestone).

**Rooms are currently hardcoded on the frontend** — `FIXED_ROOMS` array in `app.js`. The `GET /rooms` endpoint exists but returns an empty list pending DB implementation.

## Known Gaps

- **`room_id` type mismatch.** The frontend and the WebSocket route address rooms by string slug (`"general"`, `"tech"`), while `rooms.id` is an integer. Wiring `endpoints/rooms.py` to `crud_room` requires picking one of the two first.
- **Messages are never persisted.** The WebSocket handler broadcasts and forgets; the `messages` table is unused.
- **`broadcast()` has no per-socket error handling.** One dead socket raises and the remaining connections in that room miss the message.
- **Only `WebSocketDisconnect` is caught.** Malformed non-JSON input escapes the handler without cleanup, leaving a stale socket registered in the room.
- **Debug echo.** The handler still replies `You wrote: {data}` as plain text; the frontend fails to parse it as JSON and silently drops it.
- **No presence roster.** `members` in the frontend is only filled from live `join` events, so joining an already-populated room shows an empty member list.

## What's Pending

- Wire `app/api/v1/endpoints/rooms.py` to `crud_room`
- Seed the 5 default rooms into the database
- Redis Pub/Sub to replace in-memory ConnectionManager
- Nginx reverse proxy with WebSocket upgrade headers
- Message history on room join (load last N messages from DB)
- Logout token blacklisting (currently stateless — logout is client-side only)
