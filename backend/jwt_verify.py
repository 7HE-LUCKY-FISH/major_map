from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt


JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"  # change later if we want to

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

if not JWT_SECRET:  # pragma: no cover - env setup
    raise ValueError("JWT_SECRET environment variable is not set")


def create_access_token(*, user_id: int) -> str:
    """Return a JWT access token for *user_id*.

    The token includes issued-at and expiration claims based on
    :mod:`ACCESS_TOKEN_EXPIRE_MINUTES` and is signed using
    :data:`JWT_SECRET` and :data:`JWT_ALGORITHM`.
    """

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user_id_cookie(request: Request) -> int:
    """Extract the user ID from the access token cookie.

    Raises :class:`fastapi.HTTPException` with status 401 for any
    problems including missing, malformed or expired tokens.
    """

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require_exp": False},  # change to True in prod
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid access token")

    try:
        return int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid access token")
