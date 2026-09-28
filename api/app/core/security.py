from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    return jwt.encode(
        {**data, "exp": expire},
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def verify_access_token(token: str) -> dict | None:
    """Return the claims of a valid token, or None if the token is rejected.

    The caller needs more than `sub`: `ver` has to be checked against the user
    row, so the whole payload comes back rather than one claim.
    """
    try:
        return jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub", "ver"]},
        )
    except jwt.InvalidTokenError:
        return None
