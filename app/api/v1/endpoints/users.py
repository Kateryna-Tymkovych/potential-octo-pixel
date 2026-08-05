from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api import deps
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def read_user_me(current_user: User = Depends(deps.get_current_user)) -> Any:
    return current_user

@router.get("/", response_model=List[UserOut], dependencies=[Depends(deps.allow_admin)])
async def read_users(db: AsyncSession = Depends(deps.get_db), skip: int = 0, limit: int = 100) -> Any:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()
