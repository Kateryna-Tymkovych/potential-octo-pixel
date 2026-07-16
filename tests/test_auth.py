def test_register(client):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_login(client):
    # Register first
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in client.cookies


def test_refresh(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    old_at = login_res.json()["access_token"]
    old_rt = client.cookies["refresh_token"]

    refresh_res = client.post("/auth/refresh")
    assert refresh_res.status_code == 200
    new_at = refresh_res.json()["access_token"]
    new_rt = client.cookies["refresh_token"]

    assert new_at != old_at
    assert new_rt != old_rt


def test_logout(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert "refresh_token" in client.cookies

    logout_res = client.post("/auth/logout")
    assert logout_res.status_code == 200
    assert "refresh_token" not in client.cookies


def test_get_me(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_rbac(client):
    # Regular user
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password", "role": "user"},
    )
    login_user = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password"},
    )
    user_token = login_user.json()["access_token"]

    # Admin user
    client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "password", "role": "admin"},
    )
    login_admin = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "password"},
    )
    admin_token = login_admin.json()["access_token"]

    # Test access
    res_user = client.get("/admin-only", headers={"Authorization": f"Bearer {user_token}"})
    assert res_user.status_code == 403

    res_admin = client.get("/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert res_admin.json()["message"] == "Hello Admin"
