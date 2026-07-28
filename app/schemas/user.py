from pydantic import BaseModel, EmailStr
from app.models.enums import UserRole
from app.schemas.base import BaseResponse

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.user

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase, BaseResponse):
    id: int
