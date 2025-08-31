import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import get_db, Base
import models
from utils.test_data import create_test_user_data, TestDataLimiter

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Freezer App API"}

def test_user_registration(setup_database):
    # Use PII-protected test data
    test_user = create_test_user_data()
    response = client.post(
        "/auth/register",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert "id" in data

def test_user_login(setup_database):
    # Use PII-protected test data
    test_user = create_test_user_data()
    # Register user first
    client.post(
        "/auth/register",
        json={
            "email": test_user["email"], 
            "password": test_user["password"],
            "full_name": test_user["full_name"]
        }
    )
    
    # Login
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_household(setup_database):
    # Register and login
    client.post("/auth/register", json={"email": "test@example.com", "password": "testpassword123"})
    login_response = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword123"})
    token = login_response.json()["access_token"]
    
    # Create household
    response = client.post(
        "/households",
        json={"name": "Test House", "description": "Test household"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test House"
    assert "invite_code" in data

def test_get_household_locations(setup_database):
    # Setup user and household
    client.post("/auth/register", json={"email": "test@example.com", "password": "testpassword123"})
    login_response = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword123"})
    token = login_response.json()["access_token"]
    
    household_response = client.post(
        "/households",
        json={"name": "Test House"},
        headers={"Authorization": f"Bearer {token}"}
    )
    household_id = household_response.json()["id"]
    
    # Get locations (should have default locations)
    response = client.get(
        f"/households/{household_id}/locations",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) == 3  # Default: freezer, fridge, pantry
    location_names = [loc["name"] for loc in locations]
    assert "Freezer" in location_names
    assert "Fridge" in location_names  
    assert "Pantry" in location_names