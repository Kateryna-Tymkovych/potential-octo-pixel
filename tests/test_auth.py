import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.token import RefreshToken

@pytest.mark.asyncio
async def test_register(client: AsyncClient, db: AsyncSession):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "role": "user"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Test duplicate registration
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "role": "user"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login(client: AsyncClient, db: AsyncSession):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123", "role": "user"}
    )

    # Success login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "refresh_token" in response.cookies

    # Wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, db: AsyncSession):
    # Login to get tokens
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "password123", "role": "user"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "password123"}
    )
    old_refresh_token = login_res.cookies.get("refresh_token")

    # Refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": old_refresh_token}
    )
    assert refresh_res.status_code == 200
    new_refresh_token = refresh_res.cookies.get("refresh_token")
    assert new_refresh_token != old_refresh_token

    # Reusing old refresh token should fail (verifies revocation)
    fail_res = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": old_refresh_token}
    )
    assert fail_res.status_code == 401

@pytest.mark.asyncio
async def test_logout(user_client: AsyncClient):
    refresh_token = user_client.cookies.get("refresh_token")

    # Logout
    logout_res = await user_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert "refresh_token" not in logout_res.cookies

    # Reusing refresh token after logout should fail (verifies revocation)
    fail_res = await user_client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_token}
    )
    assert fail_res.status_code == 401
