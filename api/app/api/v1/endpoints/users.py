from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.crud import crud_user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.rate_limit import login_limiter

router = APIRouter(prefix="/users", tags=["auth"])


def _enforce_login_rate_limit(request: Request, username: str) -> None:
    """Two independent budgets, because they stop different attacks.

    Per address stops one host walking a password list, and keeps Argon2 -- which
    is expensive on purpose -- from being turned into a CPU exhaustion lever.
    Per username stops many hosts converging on a single account.

    `request.client` is the immediate peer, so behind a proxy every user shares
    one key until uvicorn is run with `--proxy-headers` and the proxy is trusted.
    """
    client = request.client.host if request.client else "unknown"

    for key in (f"ip:{client}", f"user:{username}"):
        wait = login_limiter.retry_after(key)

        if wait is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Try again shortly.",
                headers={"Retry-After": str(max(1, int(wait)))},
            )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserCreate, db: DbSession) -> User:
    """Create a new user: hash the password and store the account."""
    if await crud_user.get_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username taken",
        )

    return await crud_user.create(db, user_in)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    """Verify credentials and return a JWT access token."""
    # Before the password check, so a rejected attempt costs no Argon2 work.
    _enforce_login_rate_limit(request, form_data.username)

    user = await crud_user.get_by_username(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        # `ver` is what a logout invalidates: it has to travel in the token.
        data={"sub": str(user.id), "ver": user.token_version},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: CurrentUser, db: DbSession) -> None:
    """Revoke every access token issued for this account so far.

    A JWT is stateless, so there is nothing to delete: the account's token
    version is bumped instead and any token carrying the old one stops
    verifying. That logs the account out everywhere, which is the intent --
    there is no per-device session to single out.
    """
    await crud_user.bump_token_version(db, current_user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    """Return the account behind the bearer token."""
    return current_user
