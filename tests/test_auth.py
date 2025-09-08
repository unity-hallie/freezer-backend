from fastapi.testclient import TestClient
from utils.test_data import create_test_user_data


def test_user_registration(client: TestClient):
    test_user = create_test_user_data()
    response = client.post(
        "/auth/register",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert "id" in data


def test_user_login(client: TestClient):
    test_user = create_test_user_data()
    client.post(
        "/auth/register",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"],
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
