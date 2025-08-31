"""
End-to-End Test: Complete Password Reset Flow
Tests the entire password reset journey with actual token usage
"""
import requests
import time
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"

# Database setup for token extraction
SQLALCHEMY_DATABASE_URL = "sqlite:///./freezer_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_reset_token_from_db(email: str) -> str:
    """Extract reset token from database for testing"""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user and user.password_reset_token:
            return user.password_reset_token
        return None
    finally:
        db.close()

def test_complete_password_reset_flow():
    """Test the complete password reset flow with real tokens"""
    
    print("🧪 Testing Complete E2E Password Reset Flow...")
    
    # 1. Register a test user
    test_email = f"e2etest_{int(time.time())}@example.com"
    original_password = "oldpassword123"
    new_password = "newpassword456"
    
    register_data = {
        "email": test_email,
        "password": original_password,
        "full_name": "E2E Test User"
    }
    
    print("1️⃣ Registering test user...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False
    
    print(f"✅ User registered: {test_email}")
    
    # 2. Verify initial login works
    print("2️⃣ Testing original login...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": original_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Initial login failed: {login_response.status_code}")
        return False
    
    print("✅ Original login successful")
    
    # 3. Request password reset
    print("3️⃣ Requesting password reset...")
    reset_request = requests.post(f"{BASE_URL}/auth/request-password-reset", json={
        "email": test_email
    })
    
    if reset_request.status_code != 200:
        print(f"❌ Password reset request failed: {reset_request.status_code}")
        return False
    
    print("✅ Password reset email sent")
    
    # 4. Get reset token from database (simulating email click)
    print("4️⃣ Extracting reset token from database...")
    reset_token = get_reset_token_from_db(test_email)
    
    if not reset_token:
        print("❌ No reset token found in database")
        return False
    
    print(f"✅ Reset token extracted: {reset_token[:20]}...")
    
    # 5. Test password reset with token
    print("5️⃣ Resetting password with token...")
    reset_response = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": reset_token,
        "new_password": new_password
    })
    
    if reset_response.status_code != 200:
        print(f"❌ Password reset failed: {reset_response.status_code}")
        print(f"Response: {reset_response.text}")
        return False
    
    print("✅ Password reset successful")
    
    # 6. Verify old password no longer works
    print("6️⃣ Testing old password (should fail)...")
    old_login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": original_password
    })
    
    if old_login_response.status_code == 200:
        print("❌ Old password still works (should have failed)")
        return False
    
    print("✅ Old password correctly rejected")
    
    # 7. Verify new password works
    print("7️⃣ Testing new password...")
    new_login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": new_password
    })
    
    if new_login_response.status_code != 200:
        print(f"❌ New password login failed: {new_login_response.status_code}")
        return False
    
    print("✅ New password login successful")
    
    # 8. Test frontend reset URL format
    print("8️⃣ Testing frontend reset URL format...")
    frontend_reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    print(f"📱 Frontend reset URL would be: {frontend_reset_url}")
    
    # 9. Test token expiration (try to use token again)
    print("9️⃣ Testing token reuse (should fail)...")
    reuse_response = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": reset_token,
        "new_password": "anothernewpassword123"
    })
    
    if reuse_response.status_code == 200:
        print("❌ Reset token was reused (should have failed)")
        return False
    
    print("✅ Token correctly invalidated after use")
    
    print("🎉 Complete E2E Password Reset Flow test passed!")
    print(f"📧 User {test_email} successfully reset password from '{original_password}' to '{new_password}'")
    
    return True

if __name__ == "__main__":
    success = test_complete_password_reset_flow()
    if not success:
        print("❌ E2E test failed")
        exit(1)
    else:
        print("✅ All E2E tests passed")