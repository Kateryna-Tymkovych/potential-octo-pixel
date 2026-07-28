from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, allow_admin
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin-only", dependencies=[Depends(allow_admin)])
async def admin_only():
    return {"message": "Welcome, Admin!"}
