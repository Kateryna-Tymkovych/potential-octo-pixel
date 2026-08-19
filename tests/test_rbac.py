from app.core.security import get_password_hash
from app.models.user import User

def create_test_user(db, email, role):
    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    return user

def test_rbac_access(client, db):
    # Create an admin and a regular user
    create_test_user(db, "admin@test.com", "admin")
    create_test_user(db, "user@test.com", "user")

    # Login as User
    login_user = client.post("/auth/login", json={"email": "user@test.com", "password": "password123"})
    user_token = login_user.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Login as Admin
    login_admin = client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Test User Access
    assert client.get("/user-only", headers=user_headers).status_code == 200
    assert client.get("/admin-only", headers=user_headers).status_code == 403

    # Test Admin Access
    assert client.get("/user-only", headers=admin_headers).status_code == 200
    assert client.get("/admin-only", headers=admin_headers).status_code == 200

    # Unauthenticated
    assert client.get("/user-only").status_code == 401
