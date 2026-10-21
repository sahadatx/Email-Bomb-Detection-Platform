from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.modules.users.models import User, UserRole


TEST_DATABASE_URL = "sqlite:///./test_user_management.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture()
def db() -> Session:
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db: Session) -> TestClient:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def admin(db: Session) -> User:
    user = User(
        email="admin@example.com",
        username="admin",
        full_name="System Administrator",
        password_hash=hash_password("AdminPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_locked=False,
        force_password_change=False,
        failed_login_attempts=0,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def viewer(db: Session) -> User:
    user = User(
        email="viewer@example.com",
        username="viewer",
        full_name="Test Viewer",
        password_hash=hash_password("ViewerPassword123!"),
        role=UserRole.VIEWER,
        is_active=True,
        is_locked=False,
        force_password_change=False,
        failed_login_attempts=0,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
