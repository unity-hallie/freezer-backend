#!/usr/bin/env python3
"""
Quick test for health check endpoints
"""
import requests
import subprocess
import time
import sys
import os
import signal

def test_health_endpoints():
    """Test health check endpoints"""
    print("🚀 Starting FastAPI server for health endpoint testing...")
    
    # Start server in background
    proc = subprocess.Popen(
        ['python3', '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8002'],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    # Give it time to start
    time.sleep(4)
    
    try:
        # Test basic health endpoint
        print("📡 Testing /health endpoint...")
        response = requests.get('http://localhost:8002/health', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ /health endpoint working")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ /health failed with status {response.status_code}")
            
        print("\n📡 Testing /api/health endpoint...")
        # Test detailed API health endpoint  
        response = requests.get('http://localhost:8002/api/health', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ /api/health endpoint working")
            data = response.json()
            print(f"Service: {data.get('service')}")
            print(f"Status: {data.get('status')}")
            print(f"Database: {data.get('checks', {}).get('database_connection')}")
            print(f"Environment: {data.get('environment')}")
        else:
            print(f"❌ /api/health failed with status {response.status_code}")
            
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
    test_health_endpoints()