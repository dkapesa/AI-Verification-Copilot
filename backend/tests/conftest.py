import os
from collections.abc import Generator

from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.deps import get_db
from app.main import app

# Import all models so Base.metadata knows about every table.
# Keep this import even if it looks unused.
from app.db import models  # noqa: F401


def _get_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not set. "
            "Create a separate test database and set TEST_DATABASE_URL before running pytest."
        )

    if "_test" not in database_url:
        raise RuntimeError(
            "Refusing to run tests because TEST_DATABASE_URL does not look like a test database. "
            "Use a dedicated database such as ai_verification_copilot_test."
        )

    return database_url


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        _get_test_database_url(),
        pool_pre_ping=True,
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def sample_case_payload() -> dict:
    return {
        "user_id": "user_test_001",
        "email": "test.user@example.com",
        "device_info": {
            "ip_country": "US",
            "device_fingerprint": "test-device-001",
            "is_vpn": False,
            "is_emulator": False,
        },
        "document_check_result": {
            "document_type": "passport",
            "document_country": "US",
            "document_valid": True,
            "face_match_score": 0.96,
        },
        "behaviour_summary": {
            "login_velocity": "normal",
            "failed_attempts": 0,
            "typing_pattern": "consistent",
        },
    }