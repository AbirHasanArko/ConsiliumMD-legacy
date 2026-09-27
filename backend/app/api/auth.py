"""Auth router."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.deps import db_dep, get_current_user
from app.models import AuditEvent, User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit import AuditService, client_ip

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(db_dep)) -> TokenResponse:
    user = db.query(User).filter_by(email=req.email).first()
    if not user or not user.is_active or not verify_password(req.password, user.password_hash):
        AuditService(db).record(
            action="auth.login_failed",
            target_type="user",
            target_id=user.id if user else None,
            actor_user_id=None,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            payload={"email": req.email},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )
    user.last_login_at = datetime.utcnow()
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    AuditService(db).record(
        action="auth.login",
        target_type="user",
        target_id=user.id,
        actor_user_id=user.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload={"email": req.email},
    )
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=_settings.jwt_access_ttl_min * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db: Session = Depends(db_dep)) -> TokenResponse:
    try:
        payload = decode_token(req.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token"
        )
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token"
        )
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive"
        )
    access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=_settings.jwt_access_ttl_min * 60,
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )
