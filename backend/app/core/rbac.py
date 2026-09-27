"""Role-based access control matrix.

The role → permission mapping is the single source of truth for what each
role can do. New permissions are added here, then checked via
`require_permission` in `app/deps.py`.
"""
from __future__ import annotations

# Role names
ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_SENIOR_CLINICIAN = "senior_clinician"
ROLE_NURSE = "nurse"

ALL_ROLES = [ROLE_ADMIN, ROLE_DOCTOR, ROLE_SENIOR_CLINICIAN, ROLE_NURSE]

# Permission names
PERM_RECOMMENDATION_VIEW = "recommendation:view"
PERM_RECOMMENDATION_ACTION = "recommendation:action"
PERM_RECOMMENDATION_REVIEW = "recommendation:review"
PERM_CASE_CREATE = "case:create"
PERM_CASE_ASSIGN = "case:assign"
PERM_USER_MANAGE = "user:manage"
PERM_AUDIT_VIEW = "audit:view"
PERM_AUDIT_EXPORT = "audit:export"

ALL_PERMISSIONS = [
    PERM_RECOMMENDATION_VIEW,
    PERM_RECOMMENDATION_ACTION,
    PERM_RECOMMENDATION_REVIEW,
    PERM_CASE_CREATE,
    PERM_CASE_ASSIGN,
    PERM_USER_MANAGE,
    PERM_AUDIT_VIEW,
    PERM_AUDIT_EXPORT,
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_ADMIN: [
        PERM_RECOMMENDATION_VIEW,
        PERM_CASE_CREATE,
        PERM_CASE_ASSIGN,
        PERM_USER_MANAGE,
        PERM_AUDIT_VIEW,
        PERM_AUDIT_EXPORT,
    ],
    ROLE_DOCTOR: [
        PERM_RECOMMENDATION_VIEW,
        PERM_RECOMMENDATION_ACTION,
        PERM_CASE_CREATE,
        PERM_CASE_ASSIGN,
    ],
    ROLE_SENIOR_CLINICIAN: [
        PERM_RECOMMENDATION_VIEW,
        PERM_RECOMMENDATION_ACTION,
        PERM_RECOMMENDATION_REVIEW,
    ],
    ROLE_NURSE: [
        PERM_RECOMMENDATION_VIEW,
    ],
}


def permissions_for(roles: list[str]) -> set[str]:
    """Union of permissions for a user's roles."""
    out: set[str] = set()
    for role in roles:
        out.update(ROLE_PERMISSIONS.get(role, []))
    return out


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])
