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

4. Create the database (the name has to match the one in `DATABASE_URL` below):

```powershell
createdb -U postgres amagi
```

5. Create a `.env` file in `api/` (see `.env.example`):

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/amagi
SECRET_KEY=<a generated random value>
```

`SECRET_KEY` signs every access token, so it has to be a real random value —
anyone who knows it can forge a token for any account. Generate one with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

6. Apply database migrations:

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

This starts PostgreSQL and the API together, and **the API container applies the
migrations itself before serving** — there is nothing left to run by hand.

Compose reads `SECRET_KEY` from `api/.env` (or from the shell environment) and
there is no default: the API container refuses to start if the variable is
missing or empty, rather than falling back to a key that is public in this repo.

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
- `POST /api/v1/users/token` - Log in and receive a JWT access token (rate limited)
- `POST /api/v1/users/logout` - Revoke every access token issued for the account
- `GET /api/v1/users/me` - Retrieve the current authenticated user
- `GET /api/v1/rooms` - List every room (requires a token)
- `GET /api/v1/rooms/{room_slug}` - Get one room, 404 if the slug matches none (requires a token)

Rooms are seeded by migration and read-only over the API: there is no endpoint to create or delete one.

## WebSocket Usage

```text
ws://localhost:8000/api/v1/ws/{room_slug}
```

Replace `{room_slug}` with a room's slug — `general`, `tech`, `random`, `ideas` or `help`.

The access token is **not** a query parameter: it is offered as a subprotocol, so it travels in the `Sec-WebSocket-Protocol` header instead of in the URL, and never reaches the server's access log.

```js
new WebSocket("ws://localhost:8000/api/v1/ws/general", ["bearer", JWT_TOKEN]);
```

The client sends a join event after connecting and then sends message payloads as JSON.

A slug no room answers to closes the socket with the application code `4004`; a rejected token is refused at the handshake and never opens one.

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

3. Use the returned `access_token` for WebSocket auth, offered as a subprotocol:

```js
new WebSocket("ws://localhost:8000/api/v1/ws/general", ["bearer", "eyJhbGciOiJI..."]);
```

## Notes

- Database URL and secret key are loaded from `.env` and validated at startup.
- Allowed CORS origins are configured in `app/core/config.py` and cover port 3000 on `localhost`, `127.0.0.1`, and `[::1]`.

## License

This project is provided as-is for learning and experimentation.
