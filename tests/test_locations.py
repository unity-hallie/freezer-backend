from fastapi.testclient import TestClient


def test_get_household_locations(authenticated_client: TestClient):
    household_response = authenticated_client.post(
        "/households", json={"name": "Test House"}
    )
    household_id = household_response.json()["id"]

    response = authenticated_client.get(f"/households/{household_id}/locations")
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) == 3  # Default: freezer, fridge, pantry
    location_names = [loc["name"] for loc in locations]
    assert "Freezer" in location_names
    assert "Fridge" in location_names
    assert "Pantry" in location_names
