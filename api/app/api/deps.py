from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import verify_access_token
from app.crud import crud_user
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/users/token")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


@asynccontextmanager
async def ws_session() -> AsyncGenerator[AsyncSession, None]:
    """A session scoped to a WebSocket handshake rather than to the socket.

    A WebSocket handler that declares `DbSession` holds that connection for the
    entire life of the socket, so N idle chatters pin N pooled connections and
    the pool is exhausted long before the process is. Only the handshake reads
    the database, so it borrows a session and hands it straight back.

    Read-only by design: unlike `get_db` there is nothing here to commit.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await _user_from_token(token, db)
    if user is None:
        raise unauthorized

    return user


async def get_current_user_ws(token: str, db: AsyncSession) -> User | None:
    """WebSocket variant: the token arrives as a subprotocol rather than in an
    Authorization header, and a rejection closes the socket instead of raising
    an HTTP error."""
    return await _user_from_token(token, db)


async def _user_from_token(token: str, db: AsyncSession) -> User | None:
    claims = verify_access_token(token=token)
    if claims is None:
        return None

    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError):
        return None

    user = await crud_user.get(db, user_id)
    if user is None:
        return None

    # A logout bumps the stored version, stranding every token issued before it.
    # The row is already loaded, so this costs no extra query.
    if claims.get("ver") != user.token_version:
        return None

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
