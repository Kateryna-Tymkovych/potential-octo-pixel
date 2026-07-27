from fastapi.testclient import TestClient

def test_create_user(client: TestClient):
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["role"] == "user"
    assert data["is_active"] is True

def test_create_duplicate_user(client: TestClient):
    payload = {"email": "duplicate@example.com", "password": "password123"}

    # First registration
    response1 = client.post("/auth/register", json=payload)
    assert response1.status_code == 200

    # Second registration with same email
    response2 = client.post("/auth/register", json=payload)
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Email already registered"

def test_register_invalid_email(client: TestClient):
    payload = {"email": "not-an-email", "password": "password123"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
