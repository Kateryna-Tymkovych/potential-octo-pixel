import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_lifecycle(client: AsyncClient):
    # 1. Register a user
    reg_response = await client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "password123",
        "role": "user"
    })
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == "user@example.com"
    assert reg_response.json()["role"] == "user"

    # 1b. Duplicate email registration should fail
    dup_response = await client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "password456",
        "role": "user"
    })
    assert dup_response.status_code == 400

    # 2. Login with incorrect credentials
    bad_login = await client.post("/auth/login", data={
        "username": "user@example.com",
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401

    # 3. Login with correct credentials
    login_response = await client.post("/auth/login", data={
        "username": "user@example.com",
        "password": "password123"
    })
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    access_token = tokens["access_token"]

    # Check refresh cookie is set
    assert "refresh_token" in login_response.cookies
    refresh_token = login_response.cookies["refresh_token"]

    # 4. Refresh tokens using the refresh cookie
    client.cookies.set("refresh_token", refresh_token)
    refresh_response = await client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    new_access_token = new_tokens["access_token"]
    assert "refresh_token" in refresh_response.cookies
    new_refresh_token = refresh_response.cookies["refresh_token"]

    # 5. Old refresh token (rotation breach/blacklist) should now fail
    client.cookies.set("refresh_token", refresh_token)
    fail_refresh_response = await client.post("/auth/refresh")
    assert fail_refresh_response.status_code == 401

    # 6. Logout
    client.cookies.set("refresh_token", new_refresh_token)
    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 200

    # 7. Old refresh token after logout should fail
    client.cookies.set("refresh_token", new_refresh_token)
    fail_refresh_response2 = await client.post("/auth/refresh")
    assert fail_refresh_response2.status_code == 401
