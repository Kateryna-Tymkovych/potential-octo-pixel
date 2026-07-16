import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import get_db
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_auth.db"

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_auth_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register a user
        reg_response = await ac.post("/auth/register", json={
            "email": "user@example.com",
            "password": "password123",
            "role": "user"
        })
        assert reg_response.status_code == 201
        assert reg_response.json()["email"] == "user@example.com"
        assert reg_response.json()["role"] == "user"

        # 1b. Duplicate email registration should fail
        dup_response = await ac.post("/auth/register", json={
            "email": "user@example.com",
            "password": "password456",
            "role": "user"
        })
        assert dup_response.status_code == 400

        # 2. Login with incorrect credentials
        bad_login = await ac.post("/auth/login", data={
            "username": "user@example.com",
            "password": "wrongpassword"
        })
        assert bad_login.status_code == 401

        # 3. Login with correct credentials
        login_response = await ac.post("/auth/login", data={
            "username": "user@example.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        access_token = tokens["access_token"]

        # Check refresh cookie is set
        assert "refresh_token" in login_response.cookies
        refresh_token = login_response.cookies["refresh_token"]

        # 4. Access protected user-only endpoint with access token
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = await ac.get("/user-only", headers=headers)
        assert user_response.status_code == 200
        assert user_response.json()["user"] == "user@example.com"

        # 5. Access protected admin-only endpoint (should fail for 'user' role)
        admin_response = await ac.get("/admin-only", headers=headers)
        assert admin_response.status_code == 403

        # 6. Refresh tokens using the refresh cookie
        ac.cookies.set("refresh_token", refresh_token)
        refresh_response = await ac.post("/auth/refresh")
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        new_access_token = new_tokens["access_token"]
        assert "refresh_token" in refresh_response.cookies
        new_refresh_token = refresh_response.cookies["refresh_token"]

        # 7. Old refresh token (rotation breach/blacklist) should now fail
        ac.cookies.set("refresh_token", refresh_token)
        fail_refresh_response = await ac.post("/auth/refresh")
        assert fail_refresh_response.status_code == 401

        # 8. Use new access token
        headers = {"Authorization": f"Bearer {new_access_token}"}
        user_response2 = await ac.get("/user-only", headers=headers)
        assert user_response2.status_code == 200

        # 9. Logout
        ac.cookies.set("refresh_token", new_refresh_token)
        logout_response = await ac.post("/auth/logout")
        assert logout_response.status_code == 200

        # 10. Old refresh token after logout should fail
        ac.cookies.set("refresh_token", new_refresh_token)
        fail_refresh_response2 = await ac.post("/auth/refresh")
        assert fail_refresh_response2.status_code == 401
