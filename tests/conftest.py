import asyncio
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # In-memory SQLite is destroyed on close, so drop_all is redundant

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

async def _get_authenticated_client(db: AsyncSession, email: str, role: str) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: db
    ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    await ac.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": role}
    )
    login_res = await ac.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"}
    )
    token = login_res.json()["access_token"]
    ac.headers["Authorization"] = f"Bearer {token}"
    return ac

@pytest.fixture
async def user_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    ac = await _get_authenticated_client(db, "user@example.com", "user")
    async with ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def admin_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    ac = await _get_authenticated_client(db, "admin@example.com", "admin")
    async with ac:
        yield ac
    app.dependency_overrides.clear()
