"""
This file contains shared fixtures for the freezer-backend tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, limiter
from database import get_db
import models
from utils.test_data import create_test_user_data

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session(tmp_path):
    """
    Creates a new database session for a test.
    """
    db_path = tmp_path / "test.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        models.Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Creates a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def authenticated_client(client):
    """
    Creates a new user and returns an authenticated client.
    """
    test_user = create_test_user_data()
    client.post(
        "/auth/register",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"],
        },
    )
    login_response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
