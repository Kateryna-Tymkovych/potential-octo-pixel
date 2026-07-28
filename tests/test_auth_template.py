import pytest
from tests.auth_utils import assert_authorization

# --- Example 1: Standard RBAC (Role Based Access Control) ---
# Use this pattern for endpoints that are restricted by Role only.
@pytest.mark.asyncio
@pytest.mark.parametrize("client_name, expected_status", [
    ("admin_client", 200),   # Admins can access
    ("user_client", 403),    # Regular users are forbidden
    ("client", 401),         # Unauthenticated guests are unauthorized
], ids=["admin", "user", "guest"])
async def test_admin_only_endpoint_template(admin_client, user_client, client, client_name, expected_status):
    """
    Standard template for testing role-restricted endpoints.

    We pass all potential client fixtures and use a mapping to select the target.
    This avoids event-loop issues with dynamic fixture resolution.
    """
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

# --- Example 2: POST with Payload ---
@pytest.mark.asyncio
@pytest.mark.parametrize("client_name, expected_status", [
    ("admin_client", 201),
    ("user_client", 201),
    ("client", 401),
], ids=["admin", "user", "guest"])
async def test_create_resource_template(admin_client, user_client, client, client_name, expected_status):
    """
    Template for testing authorization on creation endpoints.
    """
    # Example usage with payload:
    # clients = {"admin_client": admin_client, "user_client": user_client, "client": client}
    # await assert_authorization(
    #     client=clients[client_name],
    #     method="POST",
    #     url="/api/v1/items",
    #     expected_status=expected_status,
    #     json={"name": "New Item"}
    # )
    pass

# --- Example 3: Resource Ownership (Owner vs Others) ---
# Use this pattern for endpoints where a user can only access their own data.
@pytest.mark.asyncio
async def test_resource_ownership_template(admin_client, user_client):
    """
    Template for testing ownership-based access control.
    """
    # 1. Verify: Owner can access their own info
    await assert_authorization(admin_client, "GET", "/api/v1/users/me", 200)

    # 2. Verify: Other user cannot access the first user's data
    # (In this example, we verify that user_client sees their own identity, not the admin's)
    response = await user_client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["email"] != "admin@example.com"
