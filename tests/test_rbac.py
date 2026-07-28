import pytest
from httpx import AsyncClient
from tests.auth_utils import assert_authorization

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
@pytest.mark.parametrize("client_name, expected_status", [
    ("admin_client", 200),
    ("user_client", 403),
    ("client", 401),
], ids=["admin", "user", "guest"])
async def test_admin_only_access(admin_client, user_client, client, client_name, expected_status):
    clients = {
        "admin_client": admin_client,
        "user_client": user_client,
        "client": client,
    }
    await assert_authorization(
        client=clients[client_name],
        method="GET",
        url="/api/v1/users/admin-only",
        expected_status=expected_status
    )
