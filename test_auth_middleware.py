"""
Test the authorization middleware DRY improvements
"""
import pytest
from fastapi.testclient import TestClient
from main import app
import os

# Set test environment
os.environ["ENVIRONMENT"] = "test"

client = TestClient(app)

def test_location_endpoints_with_middleware(authenticated_client: TestClient):
    """Test that location endpoints work with the new middleware"""
    
    # Create household
    household_data = {"name": "Test Household"}
    response = authenticated_client.post("/households", json=household_data)
    assert response.status_code == 200
    household_id = response.json()["id"]
    
    # Create location
    location_data = {
        "name": "Test Location", 
        "location_type": "refrigerator"
    }
    response = authenticated_client.post(f"/households/{household_id}/locations", json=location_data)
    assert response.status_code == 200
    location_id = response.json()["id"]
    
    # Test UPDATE location with middleware (should work)
    update_data = {"name": "Updated Location", "location_type": "freezer"}
    response = authenticated_client.put(f"/locations/{location_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Location"
    
    # Test DELETE location with middleware (should work)
    response = authenticated_client.delete(f"/locations/{location_id}")
    assert response.status_code == 200


def test_item_endpoints_with_middleware(authenticated_client: TestClient):
    """Test that item endpoints work with the new middleware"""
    
    # Create household and location
    household_data = {"name": "Test Household 2"}
    response = authenticated_client.post("/households", json=household_data)
    household_id = response.json()["id"]
    
    location_data = {
        "name": "Test Location 2",
        "location_type": "refrigerator"
    }
    response = authenticated_client.post(f"/households/{household_id}/locations", json=location_data)
    location_id = response.json()["id"]
    
    # Create item
    item_data = {
        "name": "Test Item",
        "quantity": 1,
        "location_id": location_id
    }
    response = authenticated_client.post(f"/locations/{location_id}/items", json=item_data)
    assert response.status_code == 200
    item_id = response.json()["id"]
    
    # Test UPDATE item with middleware (should work)
    update_data = {"name": "Updated Item", "quantity": 2}
    response = authenticated_client.put(f"/items/{item_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Item"
    
    # Test DELETE item with middleware (should work)  
    response = authenticated_client.delete(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"


def test_unauthorized_access_blocked(client: TestClient):
    """Test that middleware properly blocks unauthorized access"""
    
    # Create user 1 and their resources
    user1_data = {"email": "user1@example.com", "password": "testpassword123", "full_name": "user1"}
    response = client.post("/auth/register", json=user1_data)
    assert response.status_code == 200
    response = client.post("/auth/login", json=user1_data)
    assert response.status_code == 200
    user1_token = response.json()["access_token"]
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Create user 2 
    user2_data = {"email": "user2@example.com", "password": "testpassword123", "full_name": "user2"}
    response = client.post("/auth/register", json=user2_data)
    assert response.status_code == 200
    response = client.post("/auth/login", json=user2_data)
    assert response.status_code == 200
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # User 1 creates household, location, and item
    household_data = {"name": "Private Household"}
    response = client.post("/households", json=household_data, headers=user1_headers)
    assert response.status_code == 200
    household_id = response.json()["id"]
    
    location_data = {
        "name": "Private Location", 
        "location_type": "refrigerator"
    }
    response = client.post(f"/households/{household_id}/locations", json=location_data, headers=user1_headers)
    assert response.status_code == 200
    location_id = response.json()["id"]
    
    item_data = {
        "name": "Private Item",
        "quantity": 1,
        "location_id": location_id
    }
    response = client.post(f"/locations/{location_id}/items", json=item_data, headers=user1_headers)
    assert response.status_code == 200
    item_id = response.json()["id"]
    
    # User 2 tries to access User 1's resources (should be blocked by middleware)
    
    # Try to update location (should fail)
    update_data = {"name": "Hacked Location", "location_type": "freezer"}
    response = client.put(f"/locations/{location_id}", json=update_data, headers=user2_headers)
    assert response.status_code == 404  # Middleware should return 404 to not reveal existence
    
    # Try to delete location (should fail)
    response = client.delete(f"/locations/{location_id}", headers=user2_headers)
    assert response.status_code == 404
    
    # Try to update item (should fail)
    update_data = {"name": "Hacked Item", "quantity": 99}
    response = client.put(f"/items/{item_id}", json=update_data, headers=user2_headers)
    assert response.status_code == 404
    
    # Try to delete item (should fail)
    response = client.delete(f"/items/{item_id}", headers=user2_headers)
    assert response.status_code == 404


if __name__ == "__main__":
    test_location_endpoints_with_middleware()
    test_item_endpoints_with_middleware()
    test_unauthorized_access_blocked()
    print("🎉 Authorization middleware DRY refactoring verified!")