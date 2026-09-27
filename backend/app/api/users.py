"""User management router (admin-only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rbac import ALL_ROLES
from app.core.security import hash_password
from app.deps import db_dep, get_current_user, require_role
from app.models import Role, User, UserRole
from app.schemas.user import (
    RoleResponse,
    UserCreateRequest,
    UserResponseAdmin,
    UserUpdateRequest,
)
from app.services.audit import AuditService, client_ip
from app.core.rbac import ROLE_ADMIN

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponseAdmin])
def list_users(
    db: Session = Depends(db_dep),
    _admin: User = Depends(require_role(ROLE_ADMIN)),
) -> list[UserResponseAdmin]:
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserResponseAdmin(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            roles=[r.name for r in u.roles],
            is_active=u.is_active,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("", response_model=UserResponseAdmin, status_code=status.HTTP_201_CREATED)
def create_user(
    req: UserCreateRequest,
    request: Request,
    db: Session = Depends(db_dep),
    admin: User = Depends(require_role(ROLE_ADMIN)),
) -> UserResponseAdmin:
    if db.query(User).filter_by(email=req.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email_already_exists"
        )
    user = User(
        email=req.email,
        full_name=req.full_name,
        password_hash=hash_password(req.password),
        is_active=req.is_active,
    )
    db.add(user)
    db.flush()

    for role_name in req.role_names:
        if role_name not in ALL_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"unknown_role:{role_name}",
            )
        role = db.query(Role).filter_by(name=role_name).first()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"unknown_role:{role_name}",
            )
        db.add(UserRole(user_id=user.id, role_id=role.id))

    AuditService(db).record(
        action="user.create",
        target_type="user",
        target_id=user.id,
        actor_user_id=admin.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload={"email": req.email, "roles": req.role_names},
    )
    db.commit()

    return UserResponseAdmin(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=req.role_names,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.patch("/{user_id}", response_model=UserResponseAdmin)
def update_user(
    user_id: UUID,
    req: UserUpdateRequest,
    request: Request,
    db: Session = Depends(db_dep),
    admin: User = Depends(require_role(ROLE_ADMIN)),
) -> UserResponseAdmin:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    if req.full_name is not None:
        user.full_name = req.full_name
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password:
        user.password_hash = hash_password(req.password)
    AuditService(db).record(
        action="user.update",
        target_type="user",
        target_id=user.id,
        actor_user_id=admin.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload={"changes": req.model_dump(exclude_unset=True)},
    )
    db.commit()
    return UserResponseAdmin(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.post("/{user_id}/roles/{role_name}", response_model=UserResponseAdmin)
def add_role(
    user_id: UUID,
    role_name: str,
    request: Request,
    db: Session = Depends(db_dep),
    admin: User = Depends(require_role(ROLE_ADMIN)),
) -> UserResponseAdmin:
    if role_name not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"unknown_role:{role_name}"
        )
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    role = db.query(Role).filter_by(name=role_name).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role_not_found")
    existing = db.query(UserRole).filter_by(user_id=user_id, role_id=role.id).first()
    if existing is None:
        db.add(UserRole(user_id=user_id, role_id=role.id))
        AuditService(db).record(
            action="user.role_add",
            target_type="user",
            target_id=user.id,
            actor_user_id=admin.id,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            payload={"role": role_name},
        )
        db.commit()
    return UserResponseAdmin(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.delete("/{user_id}/roles/{role_name}", response_model=UserResponseAdmin)
def remove_role(
    user_id: UUID,
    role_name: str,
    request: Request,
    db: Session = Depends(db_dep),
    admin: User = Depends(require_role(ROLE_ADMIN)),
) -> UserResponseAdmin:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    role = db.query(Role).filter_by(name=role_name).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role_not_found")
    existing = db.query(UserRole).filter_by(user_id=user_id, role_id=role.id).first()
    if existing is not None:
        db.delete(existing)
        AuditService(db).record(
            action="user.role_remove",
            target_type="user",
            target_id=user.id,
            actor_user_id=admin.id,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            payload={"role": role_name},
        )
        db.commit()
    return UserResponseAdmin(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.get("/_roles", response_model=list[RoleResponse])
def list_roles(_: User = Depends(get_current_user)) -> list[RoleResponse]:
    # Exposed for the admin UI; authenticated users only.
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        return [
            RoleResponse(id=r.id, name=r.name, description=r.description)
            for r in roles
        ]
    finally:
        db.close()
