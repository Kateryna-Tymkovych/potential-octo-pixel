from fastapi.testclient import TestClient

def test_login_success(client: TestClient):
    # Register user first
    reg_response = client.post(
        "/auth/register",
        json={"email": "login_test@example.com", "password": "password123"}
    )
    assert reg_response.status_code == 200

    # Try login
    login_response = client.post(
        "/auth/login",
        data={"username": "login_test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Assert refresh token was set in cookie
    assert "refresh_token" in client.cookies
    assert client.cookies.get("refresh_token") is not None

def test_login_failure(client: TestClient):
    # Try logging in with unregistered user
    login_response = client.post(
        "/auth/login",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )
    assert login_response.status_code == 401

def test_refresh_token_rotation(client: TestClient):
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "rotate_test@example.com", "password": "password123"}
    )
    login_response = client.post(
        "/auth/login",
        data={"username": "rotate_test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    first_access_token = login_response.json()["access_token"]
    first_refresh_token = client.cookies.get("refresh_token")
    assert first_refresh_token is not None

    # Do rotation
    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    second_access_token = refresh_response.json()["access_token"]
    second_refresh_token = client.cookies.get("refresh_token")

    assert first_access_token != second_access_token
    assert first_refresh_token != second_refresh_token
    assert second_refresh_token is not None

    # Try using the OLD refresh token again (should fail due to revocation/reuse detection)
    client.cookies.set("refresh_token", first_refresh_token)
    failed_refresh_response = client.post("/auth/refresh")
    assert failed_refresh_response.status_code == 401

def test_logout(client: TestClient):
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "logout_test@example.com", "password": "password123"}
    )
    client.post(
        "/auth/login",
        data={"username": "logout_test@example.com", "password": "password123"}
    )
    assert "refresh_token" in client.cookies

    # Logout
    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"msg": "Successfully logged out"}

    # Trying to refresh after logout should fail (token is deleted/expired or revoked)
    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 401
