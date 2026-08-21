# Amagi

A realtime chat web app built with FastAPI, WebSockets, and a Next.js frontend.

## Overview

Amagi provides a chat application backend with user registration, JWT authentication, and WebSocket-powered room chat. The API is implemented in Python using FastAPI and async SQLAlchemy, laid out in the conventional layered structure (`api/app/`), while the frontend is a Next.js + TypeScript client in `web/`.

## Features

- User registration and login
- JWT access tokens for API and WebSocket authentication
- WebSocket room connections with room-based message broadcasts
- Async database access with SQLAlchemy and PostgreSQL
- Alembic migrations for database schema management
- Versioned API surface under `/api/v1`
- Pytest suite covering the endpoints and the connection manager

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy asyncio + asyncpg
- Alembic
- Pydantic / pydantic-settings
- JWT authentication (PyJWT) with Argon2 password hashing (pwdlib)
- Next.js (App Router) with React, TypeScript, and Tailwind CSS

## Repository Structure

```
Amagi/
├── api/                  # FastAPI project root
│   ├── app/              # Application package
│   │   ├── main.py       # Application entrypoint
│   │   ├── api/          # Routers, endpoints and shared dependencies
│   │   ├── core/         # Config, database engine, security primitives
│   │   ├── crud/         # Reusable database operations
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (WebSocket connection manager)
│   │   └── utils/        # Helpers
│   ├── alembic/          # Migration configuration and versions
│   ├── tests/            # Test suite
│   ├── pyproject.toml    # Dependencies and package metadata
│   ├── Dockerfile
│   └── docker-compose.yml
└── web/                  # Next.js frontend
    ├── app/              # App Router entry: layout, global styles, page
    ├── components/       # Auth, rooms, and chat screens
    ├── hooks/            # Session and WebSocket hooks
    ├── lib/              # Config, types, and client-side helpers
    └── package.json
```

## Prerequisites

- Python 3.11 or newer
- PostgreSQL (or Docker, which brings its own)
- `pip` package manager
- Node.js 20 or newer and `pnpm` (for the frontend)

## Backend Setup

1. Move into the API project root:

```powershell
cd api
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install the project and its development extras:

```powershell
pip install -e ".[dev]"
```

4. Create a `.env` file in `api/` (see `.env.example`):

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/amagi
SECRET_KEY=your-secret-key
```

5. Apply database migrations:

```powershell
alembic upgrade head
```

## Running the Backend

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### With Docker

```powershell
cd api
docker compose up --build
```

This starts PostgreSQL and the API together. Migrations still have to be applied against the running database.

## Running the Tests

```powershell
cd api
pytest
```

The suite runs against a throwaway SQLite database, so no PostgreSQL instance is required.

## Frontend Usage

The frontend client lives in `web/` and uses **pnpm**:

```powershell
cd web
pnpm install
pnpm dev
```

Then open `http://localhost:3000`.

By default the client talks to `http://localhost:8000/api/v1`. To point it elsewhere, copy `web/.env.example` to `web/.env.local` and edit `NEXT_PUBLIC_API_BASE` and `NEXT_PUBLIC_WS_BASE`. Note that the API matches CORS origins exactly, so the host you open must be listed in `settings.cors_origins`.

## API Endpoints

All routes are mounted under the `/api/v1` prefix.

- `POST /api/v1/users/register` - Register a new user
- `POST /api/v1/users/token` - Log in and receive a JWT access token
- `GET /api/v1/users/me` - Retrieve the current authenticated user
- `GET /api/v1/rooms/` - Get rooms (currently a placeholder)
- `POST /api/v1/rooms/` - Create a room (currently a placeholder)
- `GET /api/v1/rooms/{room_id}` - Get room details (currently a placeholder)
- `DELETE /api/v1/rooms/{room_id}` - Delete a room (currently a placeholder)

## WebSocket Usage

```text
ws://localhost:8000/api/v1/ws/{room_id}?token={JWT_TOKEN}
```

Replace `{room_id}` with the room identifier and `{JWT_TOKEN}` with a valid JWT obtained from `/api/v1/users/token`. The client sends a join event after connecting and then sends message payloads as JSON.

## Example Auth Flow

1. Register a user:

```http
POST /api/v1/users/register
Content-Type: application/json

{
  "username": "alice",
  "password": "password123"
}
```

2. Log in for a token:

```http
POST /api/v1/users/token
Content-Type: application/x-www-form-urlencoded

username=alice&password=password123
```

3. Use the returned `access_token` for WebSocket auth:

```text
ws://localhost:8000/api/v1/ws/room1?token=eyJhbGciOiJI...
```

## Notes

- The `rooms` endpoints are still placeholders; the queries they need already live in `app/crud/crud_room.py`.
- Database URL and secret key are loaded from `.env` and validated at startup.
- Allowed CORS origins are configured in `app/core/config.py` and cover port 3000 on `localhost`, `127.0.0.1`, and `[::1]`.

## License

This project is provided as-is for learning and experimentation.
