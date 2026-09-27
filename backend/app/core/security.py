"""Password hashing and JWT helpers."""
from __future__ import annotations

import time
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_settings = get_settings()


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def _now_ts() -> int:
    # Use epoch seconds directly to avoid naive-vs-aware datetime ambiguity.
    return int(time.time())


def _encode(payload: dict[str, Any], ttl_minutes: int) -> str:
    now_ts = _now_ts()
    payload = {
        **payload,
        "iat": now_ts,
        "exp": now_ts + ttl_minutes * 60,
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_alg)


def create_access_token(
    subject: str, claims: dict[str, Any] | None = None
) -> str:
    return _encode(
        {"sub": subject, "type": "access", **(claims or {})},
        _settings.jwt_access_ttl_min,
    )


def create_refresh_token(subject: str) -> str:
    return _encode({"sub": subject, "type": "refresh"}, _settings.jwt_refresh_ttl_min)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_alg])
    except JWTError as exc:
        raise ValueError("invalid_token") from exc
