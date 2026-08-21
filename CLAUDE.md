# Amagi — Claude Context File

Real-time multi-room chat application. Python/FastAPI backend, vanilla JS + Alpine.js frontend. No frontend framework, no ORM magic — raw async SQLAlchemy against PostgreSQL.

## Project Structure

```
relay/
├── backend/
│   ├── main.py              # FastAPI app, CORS, lifespan, router registration
│   ├── database.py          # Engine, AsyncSessionLocal, Base, get_db dependency
│   ├── models.py            # SQLAlchemy models: User, Room, RoomMembers, Message
│   ├── schemas.py           # Pydantic models for request/response validation
│   ├── auth.py              # Password hashing, JWT creation/verification, get_current_user
│   ├── config.py            # Pydantic Settings from .env
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── env.py           # Async-compatible Alembic config
│   └── routers/
│       ├── __init__.py
│       ├── users.py         # POST /users/register, POST /users/token, GET /users/me
│       ├── rooms.py         # GET/POST/DELETE /rooms (stubs, pending DB wiring)
│       └── websocket.py     # WebSocket endpoint + ConnectionManager
└── frontend/
    ├── index.html           # Single page, three screens via Alpine.js
    ├── style.css
    └── app.js               # Alpine app() component — all state and logic
```

## Running the Project

**Backend:**
```bash
cd backend
uvicorn main:app --reload
# runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
python -m http.server 3000 --bind 127.0.0.1
# open http://127.0.0.1:3000
```

**Database migrations:**
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Environment Variables

File: `backend/.env`

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
SECRET_KEY=your-secret-key-here
```

`config.py` loads these via Pydantic Settings. `DATABASE_URL` must use the `postgresql+asyncpg://` driver prefix for async SQLAlchemy to work.

## Auth Flow

- Passwords hashed with **Argon2** via `pwdlib`
- Tokens are **JWT** signed with `SECRET_KEY`, containing `sub` (user ID) and `exp`
- REST endpoints use `Depends(get_current_user)` which reads from `Authorization: Bearer` header via `oauth2_scheme`
- WebSocket endpoints can't use the Authorization header — token is passed as a query param `?token=...` and verified via `get_current_user_ws(token, db)`
- Token expiry is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30)

## WebSocket Protocol

**Connection URL:** `ws://localhost:8000/ws/{room_id}?token={jwt}`

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

**Alembic owns schema** — never use `Base.metadata.create_all()` alongside Alembic. Run migrations manually before starting the server.

**ConnectionManager is in-memory** — works for a single process. Horizontal scaling requires replacing it with Redis Pub/Sub (planned milestone).

**Rooms are currently hardcoded on the frontend** — `FIXED_ROOMS` array in `app.js`. The `GET /rooms` endpoint exists but returns an empty list pending DB implementation.

## What's Pending

- Wire `routers/rooms.py` endpoints to actual DB queries
- Seed the 5 default rooms into the database
- Redis Pub/Sub to replace in-memory ConnectionManager
- Docker + Docker Compose setup
- Nginx reverse proxy with WebSocket upgrade headers
- Message history on room join (load last N messages from DB)
- Logout token blacklisting (currently stateless — logout is client-side only)