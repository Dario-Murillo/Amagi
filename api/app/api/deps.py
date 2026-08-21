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
    """WebSocket variant: the handshake cannot carry an Authorization header, so
    the token arrives as a query param and a rejection closes the socket instead
    of raising an HTTP error."""
    return await _user_from_token(token, db)


async def _user_from_token(token: str, db: AsyncSession) -> User | None:
    user_id = verify_access_token(token=token)
    if user_id is None:
        return None

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return None

    return await crud_user.get(db, user_id_int)


CurrentUser = Annotated[User, Depends(get_current_user)]
