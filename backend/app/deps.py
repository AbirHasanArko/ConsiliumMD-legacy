"""FastAPI dependencies: DB session, current user, role/permission guards."""
from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.rbac import (
    ALL_PERMISSIONS,
    permissions_for,
    role_has_permission,
)
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

_settings = get_settings()


def db_dep() -> Generator[Session, None, None]:
    yield from get_db()


def _extract_bearer(auth_header: str | None) -> str:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_or_invalid_authorization",
        )
    return auth_header.split(" ", 1)[1]


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(db_dep),
) -> User:
    token = _extract_bearer(authorization)
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="wrong_token_type"
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
        )
    try:
        user_id = UUID(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token"
        )
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive"
        )
    # Stash the request for audit writers to access later.
    request.state.current_user = user
    return user


def current_user_permissions(user: User = Depends(get_current_user)) -> set[str]:
    role_names = [r.name for r in user.roles]
    return permissions_for(role_names)


def require_role(*allowed_roles: str):
    """Dependency: allow only users whose roles include any of allowed_roles."""

    def _dep(user: User = Depends(get_current_user)) -> User:
        role_names = [r.name for r in user.roles]
        if not any(r in role_names for r in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role_required: {','.join(allowed_roles)}",
            )
        return user

    return _dep


def require_permission(permission: str):
    if permission not in ALL_PERMISSIONS:
        raise ValueError(f"unknown_permission:{permission}")

    def _dep(user: User = Depends(get_current_user)) -> User:
        role_names = [r.name for r in user.roles]
        if not any(role_has_permission(r, permission) for r in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"permission_required: {permission}",
            )
        return user

    return _dep
