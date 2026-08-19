def test_auth_lifecycle(client):
    # 1. Register
    reg_data = {"email": "test@example.com", "password": "password123"}
    response = client.post("/auth/register", json=reg_data)
    assert response.status_code == 200
    assert response.json()["email"] == reg_data["email"]

    # 2. Login
    login_response = client.post("/auth/login", json=reg_data)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert "refresh_token" in login_response.cookies

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.cookies["refresh_token"]

    # 3. Refresh
    refresh_response = client.post("/auth/refresh", cookies={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()
    assert "refresh_token" in refresh_response.cookies

    new_refresh_token = refresh_response.cookies["refresh_token"]
    assert new_refresh_token != refresh_token

    # 4. Try old refresh token (should fail as it's revoked)
    old_refresh_response = client.post("/auth/refresh", cookies={"refresh_token": refresh_token})
    assert old_refresh_response.status_code == 401

    # 5. Logout
    logout_response = client.post("/auth/logout", cookies={"refresh_token": new_refresh_token})
    assert logout_response.status_code == 200

    # 6. Try use revoked token after logout
    after_logout_refresh = client.post("/auth/refresh", cookies={"refresh_token": new_refresh_token})
    assert after_logout_refresh.status_code == 401
