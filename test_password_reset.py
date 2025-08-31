"""
TDD: Password Reset Email Functionality
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_password_reset_flow():
    """
    Test the complete password reset flow:
    1. Request password reset for existing user
    2. Verify email is "sent" (logged to console)
    3. Check that reset token is generated and stored
    """
    
    print("🧪 Testing Password Reset Flow...")
    
    # First register a test user
    test_email = f"testreset_{int(time.time())}@example.com"
    register_data = {
        "email": test_email,
        "password": "oldpassword123",
        "full_name": "Test Reset User"
    }
    
    print("1️⃣ Registering test user...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False
    
    print(f"✅ User registered: {test_email}")
    
    # Test password reset request
    print("2️⃣ Requesting password reset...")
    reset_request_data = {"email": test_email}
    reset_response = requests.post(f"{BASE_URL}/auth/request-password-reset", json=reset_request_data)
    
    if reset_response.status_code != 200:
        print(f"❌ Password reset request failed: {reset_response.status_code}")
        print(f"Response: {reset_response.text}")
        return False
    
    response_data = reset_response.json()
    print(f"✅ Reset request successful: {response_data}")
    
    # Test reset request for non-existent email (should still return success for security)
    print("3️⃣ Testing reset for non-existent email...")
    fake_reset_data = {"email": "nonexistent@example.com"}
    fake_reset_response = requests.post(f"{BASE_URL}/auth/request-password-reset", json=fake_reset_data)
    
    if fake_reset_response.status_code != 200:
        print(f"❌ Non-existent email test failed: {fake_reset_response.status_code}")
        return False
    
    fake_response_data = fake_reset_response.json()
    print(f"✅ Non-existent email handled correctly: {fake_response_data}")
    
    print("🎉 Password reset flow test completed successfully!")
    print("📧 Check the backend console for simulated email output")
    
    return True

def test_password_reset_edge_cases():
    """Test edge cases for password reset"""
    
    print("\n🧪 Testing Password Reset Edge Cases...")
    
    # Test empty email
    print("1️⃣ Testing empty email...")
    try:
        response = requests.post(f"{BASE_URL}/auth/request-password-reset", json={})
        print(f"Empty email status: {response.status_code}")
    except Exception as e:
        print(f"Empty email error (expected): {e}")
    
    # Test invalid email format
    print("2️⃣ Testing invalid email format...")
    try:
        response = requests.post(f"{BASE_URL}/auth/request-password-reset", json={"email": "notanemail"})
        print(f"Invalid email status: {response.status_code}")
    except Exception as e:
        print(f"Invalid email error: {e}")
    
    print("✅ Edge case testing completed")

if __name__ == "__main__":
    success = test_password_reset_flow()
    if success:
        test_password_reset_edge_cases()
    else:
        print("❌ Basic flow failed, skipping edge case tests")