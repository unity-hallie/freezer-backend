#!/usr/bin/env python3
"""
Test rate limiting functionality for API abuse prevention
"""
import requests
import subprocess
import time
import sys
import os
from utils.test_data import create_test_user_data

def test_rate_limiting():
    """Test API rate limiting on critical endpoints"""
    print("🚀 Starting FastAPI server for rate limiting testing...")
    
    # Start server in background
    proc = subprocess.Popen(
        ['python3', '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8003'],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    # Give it time to start
    time.sleep(4)
    
    try:
        base_url = 'http://localhost:8003'
        
        # Test registration rate limiting (3/minute limit)
        print("📧 Testing registration rate limiting (3/minute)...")
        registration_success = 0
        registration_blocked = 0
        
        for i in range(5):  # Try 5 registrations
            user_data = create_test_user_data()
            response = requests.post(f'{base_url}/auth/register', 
                                   json=user_data, timeout=5)
            if response.status_code == 200:
                registration_success += 1
                print(f"  ✅ Registration {i+1}: Success (status: {response.status_code})")
            elif response.status_code == 429:  # Rate limited
                registration_blocked += 1
                print(f"  🛑 Registration {i+1}: Rate limited (status: {response.status_code})")
            else:
                print(f"  ❓ Registration {i+1}: Other response (status: {response.status_code})")
            
            time.sleep(1)  # Small delay between requests
        
        print(f"📊 Registration results: {registration_success} success, {registration_blocked} blocked")
        
        # Test login rate limiting (10/minute limit)  
        print("\n🔐 Testing login rate limiting (10/minute)...")
        login_attempts = 0
        login_blocked = 0
        
        for i in range(12):  # Try 12 login attempts
            response = requests.post(f'{base_url}/auth/login', 
                                   json={"email": "test@example.com", "password": "wrongpass"},
                                   timeout=5)
            if response.status_code == 429:  # Rate limited
                login_blocked += 1
                print(f"  🛑 Login {i+1}: Rate limited")
                break  # Stop after first rate limit
            else:
                login_attempts += 1
                print(f"  ⏸️  Login {i+1}: Allowed (status: {response.status_code})")
        
        print(f"📊 Login results: {login_attempts} attempts before rate limiting")
        
        # Test that rate limiting is working
        if registration_blocked > 0 or login_blocked > 0:
            print("✅ Rate limiting is working - requests were blocked after limits exceeded")
        else:
            print("⚠️  Rate limiting may not be working - no requests were blocked")
            
        # Test health endpoints are NOT rate limited (important for monitoring)
        print("\n🏥 Testing health endpoints are not rate limited...")
        health_requests = 0
        for i in range(3):
            response = requests.get(f'{base_url}/health', timeout=5)
            if response.status_code == 200:
                health_requests += 1
        
        if health_requests == 3:
            print("✅ Health endpoints accessible (not rate limited)")
        else:
            print("❌ Health endpoints may be rate limited")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        
    finally:
        # Clean up server
        print("\n🛑 Stopping server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    # Set test environment
    os.environ['ENVIRONMENT'] = 'test'
    test_rate_limiting()