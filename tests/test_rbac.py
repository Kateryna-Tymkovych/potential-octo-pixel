import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_me(user_client: AsyncClient):
    # Success
    response = await user_client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"

    # Unauthorized
    del user_client.headers["Authorization"]
    response = await user_client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_only_access(admin_client: AsyncClient, user_client: AsyncClient, client: AsyncClient):
    # Success for admin
    response = await admin_client.get("/api/v1/users/admin-only")
    assert response.status_code == 200

    # Forbidden for user
    response = await user_client.get("/api/v1/users/admin-only")
    assert response.status_code == 403

    # Unauthorized for guest
    response = await client.get("/api/v1/users/admin-only")
    assert response.status_code == 401
