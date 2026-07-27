from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token

def test_rbac_access(client: TestClient, db: Session):
    # 1. Create users with dummy password hashes (avoiding expensive CPU-bound hashing)
    regular_user = User(
        email="user@example.com",
        hashed_password="dummy_hash",
        role="user",
        is_active=True
    )
    admin_user = User(
        email="admin@example.com",
        hashed_password="dummy_hash",
        role="admin",
        is_active=True
    )
    # Batch insert users and commit in a single transaction
    db.add_all([regular_user, admin_user])
    db.commit()

    # 2. Generate tokens
    user_token = create_access_token(data={"sub": str(regular_user.id)})
    admin_token = create_access_token(data={"sub": str(admin_user.id)})

    # Test case: No token (401)
    response = client.get("/api/user-area")
    assert response.status_code == 401

    response = client.get("/api/admin-only")
    assert response.status_code == 401

    # Test case: Regular user on /api/user-area (200)
    response = client.get(
        "/api/user-area",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello User"}

    # Test case: Regular user on /api/admin-only (403)
    response = client.get(
        "/api/admin-only",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

    # Test case: Admin user on /api/user-area (200)
    response = client.get(
        "/api/user-area",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello User"}

    # Test case: Admin user on /api/admin-only (200)
    response = client.get(
        "/api/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello Admin"}
