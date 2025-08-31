"""
Test the exact API flow that the frontend is using
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_full_user_flow():
    """Test the complete flow: register -> login -> create household -> access household"""
    
    print("🧪 Testing complete user flow...")
    
    # 1. Register a user
    print("1️⃣ Registering user...")
    register_data = {
        "email": "test2@example.com",
        "password": "testpass123", 
        "full_name": "Test User"
    }
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Register status: {register_response.status_code}")
    if register_response.status_code != 200:
        print(f"Register failed: {register_response.text}")
        return
    
    # 2. Login
    print("2️⃣ Logging in...")
    login_data = {
        "email": "test2@example.com",
        "password": "testpass123"
    }
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login status: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create household (this should auto-add user as member)
    print("3️⃣ Creating household...")
    household_data = {
        "name": "Test Household",
        "description": "My test household"
    }
    household_response = requests.post(f"{BASE_URL}/households", json=household_data, headers=headers)
    print(f"Create household status: {household_response.status_code}")
    if household_response.status_code != 200:
        print(f"Create household failed: {household_response.text}")
        return
    
    household = household_response.json()
    print(f"Created household: {household}")
    
    # 4. Get user households (this is failing with 403 in frontend)
    print("4️⃣ Getting user households...")
    households_response = requests.get(f"{BASE_URL}/households", headers=headers)
    print(f"Get households status: {households_response.status_code}")
    print(f"Get households response: {households_response.text}")
    
    if households_response.status_code == 200:
        households = households_response.json()
        print(f"✅ SUCCESS: User can access {len(households)} households")
    else:
        print(f"❌ FAILED: Cannot access households - {households_response.status_code}")
        print("This reproduces the bug!")
    
if __name__ == "__main__":
    test_full_user_flow()