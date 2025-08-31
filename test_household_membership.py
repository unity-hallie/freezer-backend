import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from test_main import setup_database
from utils.test_data import create_test_user_data

client = TestClient(app)

def test_owner_is_household_member_after_creation(setup_database):
    """Test that household owner is automatically a member and can access household operations"""
    
    # Use PII-protected test data
    test_user = create_test_user_data()
    
    # Register user
    register_response = client.post("/auth/register", json={
        "email": test_user["email"], 
        "password": test_user["password"]
    })
    assert register_response.status_code == 200
    
    # Login 
    login_response = client.post("/auth/login", json={
        "email": test_user["email"], 
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create household
    household_response = client.post("/households", json={
        "name": "Test House",
        "description": "Test household"  
    }, headers=headers)
    assert household_response.status_code == 200
    household = household_response.json()
    
    # Owner should be able to access their household (currently failing with 403)
    households_response = client.get("/households", headers=headers)
    assert households_response.status_code == 200
    households = households_response.json()
    assert len(households) == 1
    assert households[0]["id"] == household["id"]
    
    # Owner should be able to add items to household locations (currently failing with 403)
    # First need locations, so let's create one
    location_response = client.post(f"/households/{household['id']}/locations", json={
        "name": "Test Freezer",
        "location_type": "freezer"
    }, headers=headers)
    assert location_response.status_code == 200
    location = location_response.json()
    
    # Now try to add an item (this should work but currently fails)
    item_response = client.post(f"/locations/{location['id']}/items", json={
        "name": "Test Item",
        "description": "Test food item",
        "quantity": 1
    }, headers=headers)
    assert item_response.status_code == 200
    
    print("✅ Household owner can access all household operations")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])