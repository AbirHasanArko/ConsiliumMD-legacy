"""Pytest fixtures: in-memory SQLite + test app + seeded demo data."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the backend root is importable when tests run from anywhere.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SEED_DEMO_DATA", "true")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: F401, E402 — register tables on Base
from app.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import _ensure_roles  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Role, User, UserRole  # noqa: E402


@pytest.fixture(scope="function")
def db_session():
    """Create all tables in a fresh in-memory SQLite, yield a session."""
    from app.db.session import engine as app_engine

    # Wipe + recreate schema in the in-memory engine so each test is isolated.
    Base.metadata.drop_all(bind=app_engine)
    Base.metadata.create_all(bind=app_engine)
    Session = sessionmaker(bind=app_engine, autoflush=False, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        Base.metadata.drop_all(bind=app_engine)


@pytest.fixture
def client(db_session):
    """FastAPI client with overridden DB dependency bound to the in-memory engine."""
    from app.db.session import engine as app_engine
    from app.db.seed import _ensure_decision_class_scopes

    # Make sure every decision class the tests reference is registered in
    # the in-scope table.
    _ensure_decision_class_scopes(db_session)
    db_session.commit()

    Session = sessionmaker(bind=app_engine, autoflush=False, expire_on_commit=False)

    def _override_get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_roles(db_session):
    return _ensure_roles(db_session)


@pytest.fixture
def admin_user(db_session, seeded_roles):
    user = User(
        email="admin@test.md",
        full_name="Admin",
        password_hash=hash_password("admin1234"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=seeded_roles["admin"].id))
    db_session.commit()
    return user


@pytest.fixture
def doctor_user(db_session, seeded_roles):
    user = User(
        email="doctor@test.md",
        full_name="Doctor",
        password_hash=hash_password("doctor1234"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=seeded_roles["doctor"].id))
    db_session.commit()
    return user


@pytest.fixture
def reviewer_user(db_session, seeded_roles):
    user = User(
        email="reviewer@test.md",
        full_name="Reviewer",
        password_hash=hash_password("reviewer1234"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        UserRole(user_id=user.id, role_id=seeded_roles["senior_clinician"].id)
    )
    db_session.commit()
    return user


@pytest.fixture
def nurse_user(db_session, seeded_roles):
    user = User(
        email="nurse@test.md",
        full_name="Nurse",
        password_hash=hash_password("nurse1234"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=seeded_roles["nurse"].id))
    db_session.commit()
    return user


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
