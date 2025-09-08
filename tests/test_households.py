from fastapi.testclient import TestClient


def test_create_household(authenticated_client: TestClient):
    response = authenticated_client.post(
        "/households",
        json={"name": "Test House", "description": "Test household"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test House"
    assert "invite_code" in data


def test_get_user_households(authenticated_client: TestClient):
    """Test that a user can get their own households."""
    # Create a household first
    response = authenticated_client.post(
        "/households",
        json={"name": "Test Household", "description": "A test household"},
    )
    assert response.status_code == 200

    # Get user households
    response = authenticated_client.get("/households")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "Test Household"
