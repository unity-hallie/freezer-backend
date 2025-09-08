from fastapi.testclient import TestClient


def test_add_item_to_location(authenticated_client: TestClient):
    household_response = authenticated_client.post(
        "/households", json={"name": "Test House"}
    )
    household_id = household_response.json()["id"]

    locations_response = authenticated_client.get(f"/households/{household_id}/locations")
    freezer_location = next(
        loc for loc in locations_response.json() if loc["name"] == "Freezer"
    )

    response = authenticated_client.post(
        f"/locations/{freezer_location['id']}/items",
        json={"name": "Ice Cream", "quantity": 1},
    )
    assert response.status_code == 200
    item = response.json()
    assert item["name"] == "Ice Cream"
    assert item["quantity"] == 1


def test_get_items_in_location(authenticated_client: TestClient):
    household_response = authenticated_client.post(
        "/households", json={"name": "Test House"}
    )
    household_id = household_response.json()["id"]

    locations_response = authenticated_client.get(f"/households/{household_id}/locations")
    freezer_location = next(
        loc for loc in locations_response.json() if loc["name"] == "Freezer"
    )

    authenticated_client.post(
        f"/locations/{freezer_location['id']}/items",
        json={"name": "Popsicles", "quantity": 12},
    )

    response = authenticated_client.get(f"/locations/{freezer_location['id']}/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == "Popsicles"
