import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.auth_utils import assert_authorization

@pytest.mark.asyncio
async def test_register(client: AsyncClient, db: AsyncSession):
    response = await assert_authorization(
        client=client,
        method="POST",
        url="/api/v1/auth/register",
        expected_status=201,
        json={"email": "test@example.com", "password": "password123"}
    )
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Test duplicate registration
    await assert_authorization(
        client=client,
        method="POST",
        url="/api/v1/auth/register",
        expected_status=400,
        json={"email": "test@example.com", "password": "password123"}
    )

@pytest.mark.asyncio
async def test_login(client: AsyncClient, db: AsyncSession):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123"}
    )

    # Success login
    response = await assert_authorization(
        client=client,
        method="POST",
        url="/api/v1/auth/login",
        expected_status=200,
        json={"email": "login@example.com", "password": "password123"}
    )
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "refresh_token" in response.cookies

    # Wrong password
    await assert_authorization(
        client=client,
        method="POST",
        url="/api/v1/auth/login",
        expected_status=401,
        json={"email": "login@example.com", "password": "wrongpassword"}
    )

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, db: AsyncSession):
    # Login to get tokens
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "password123"}
    )
    old_refresh_token = login_res.cookies.get("refresh_token")

    # Refresh
    refresh_res = await assert_authorization(
        client=client,
        method="POST",
        url="/api/v1/auth/refresh",
        expected_status=200,
        cookies={"refresh_token": old_refresh_token}
    )
    new_refresh_token = refresh_res.cookies.get("refresh_token")
    assert new_refresh_token != old_refresh_token

    # Reusing old refresh token should fail (verifies revocation)
    await assert_authorization(
        client=client,
        method="POST",
        url="/api/v1/auth/refresh",
        expected_status=401,
        cookies={"refresh_token": old_refresh_token}
    )

@pytest.mark.asyncio
async def test_logout(user_client: AsyncClient):
    refresh_token = user_client.cookies.get("refresh_token")

    # Logout
    await assert_authorization(
        client=user_client,
        method="POST",
        url="/api/v1/auth/logout",
        expected_status=200
    )

    # Reusing refresh token after logout should fail (verifies revocation)
    await assert_authorization(
        client=user_client,
        method="POST",
        url="/api/v1/auth/refresh",
        expected_status=401,
        cookies={"refresh_token": refresh_token}
    )
