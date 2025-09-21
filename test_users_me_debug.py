"""
Test specifically for the /users/me endpoint that's failing in production
"""
import pytest
from fastapi.testclient import TestClient


def test_users_me_endpoint_exists(authenticated_client: TestClient):
    """Test that /users/me endpoint works locally"""
    response = authenticated_client.get("/users/me")

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    assert "email" in response.json()
    print("✅ /users/me endpoint works locally!")


def test_users_me_without_auth(client: TestClient):
    """Test /users/me without authentication"""
    response = client.get("/users/me")

    print(f"Unauthenticated status: {response.status_code}")
    print(f"Unauthenticated response: {response.json()}")

    assert response.status_code == 401
    print("✅ /users/me properly rejects unauthenticated requests!")


def test_check_registered_routes(client: TestClient):
    """Check what routes are actually registered"""
    # Get OpenAPI spec to see registered routes
    response = client.get("/openapi.json")
    openapi_spec = response.json()

    paths = openapi_spec.get("paths", {})
    user_paths = {path: methods for path, methods in paths.items() if "user" in path.lower()}

    print("=== REGISTERED USER ROUTES ===")
    for path, methods in user_paths.items():
        print(f"  {path}: {list(methods.keys())}")

    # Specifically check for /users/me
    assert "/users/me" in paths, f"Expected /users/me in paths. Found: {list(paths.keys())}"
    assert "get" in paths["/users/me"], f"/users/me should have GET method"

    print("✅ /users/me is properly registered!")