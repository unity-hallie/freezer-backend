"""
Simple test for the DRY middleware refactoring
"""
import pytest
from fastapi.testclient import TestClient


def test_middleware_dry_refactoring(authenticated_client: TestClient):
    """Test that the DRY middleware refactoring works correctly"""
    
    # Create household
    household_data = {"name": "DRY Test Household"}
    response = authenticated_client.post("/households", json=household_data)
    assert response.status_code == 200
    household_id = response.json()["id"]
    
    # Create location (this should work)
    location_data = {"name": "Test Location", "location_type": "refrigerator"}
    response = authenticated_client.post(f"/households/{household_id}/locations", json=location_data)
    assert response.status_code == 200
    location_id = response.json()["id"]
    
    # Test location endpoints use the new verify_location_access function
    # UPDATE location (should work with DRY middleware)
    update_data = {"name": "Updated Location", "location_type": "freezer"}
    response = authenticated_client.put(f"/locations/{location_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Location"
    
    # Create item
    item_data = {"name": "Test Item", "quantity": 1, "location_id": location_id}
    response = authenticated_client.post(f"/locations/{location_id}/items", json=item_data)
    assert response.status_code == 200
    item_id = response.json()["id"]
    
    # Test item endpoints use the new verify_item_access function
    # GET item (should work with DRY middleware)
    response = authenticated_client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"
    
    # UPDATE item (should work with DRY middleware)
    update_data = {"name": "Updated Item", "quantity": 2}
    response = authenticated_client.put(f"/items/{item_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Item"
    
    # DELETE item (should work with DRY middleware)
    response = authenticated_client.delete(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"
    
    # DELETE location (should work with DRY middleware)
    response = authenticated_client.delete(f"/locations/{location_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Location deleted successfully"
    
    print("✅ DRY middleware refactoring verified successfully!")
