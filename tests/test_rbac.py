import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rbac_flows(client: AsyncClient):
    # Register both a user and an admin
    await client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "user123",
        "role": "user"
    })

    await client.post("/auth/register", json={
        "email": "admin@example.com",
        "password": "admin123",
        "role": "admin"
    })

    # Login both
    login_user = await client.post("/auth/login", data={"username": "user@example.com", "password": "user123"})
    user_token = login_user.json()["access_token"]

    login_admin = await client.post("/auth/login", data={"username": "admin@example.com", "password": "admin123"})
    admin_token = login_admin.json()["access_token"]

    # 1. Missing Token -> 401 Unauthorized for both user-only and admin-only
    resp = await client.get("/user-only")
    assert resp.status_code == 401

    resp = await client.get("/admin-only")
    assert resp.status_code == 401

    # 2. User Token -> access /user-only (200), access /admin-only (403)
    user_headers = {"Authorization": f"Bearer {user_token}"}

    resp = await client.get("/user-only", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["user"] == "user@example.com"

    resp = await client.get("/admin-only", headers=user_headers)
    assert resp.status_code == 403

    # 3. Admin Token -> access both /user-only (200) and /admin-only (200)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await client.get("/user-only", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["user"] == "admin@example.com"

    resp = await client.get("/admin-only", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["user"] == "admin@example.com"
