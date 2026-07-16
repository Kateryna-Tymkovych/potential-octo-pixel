import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

@pytest.mark.asyncio
async def test_get_db():
    db_generator = get_db()
    db = await db_generator.__anext__()
    try:
        assert isinstance(db, AsyncSession)
        result = await db.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        try:
            await db_generator.__anext__()
        except StopAsyncIteration:
            pass
