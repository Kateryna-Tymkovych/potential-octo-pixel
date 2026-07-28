from typing import Annotated
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user

class RoleChecker:
    _hierarchy = {
        UserRole.admin: 100,
        UserRole.user: 10,
        UserRole.guest: 1
    }

    def __init__(self, required_role: UserRole):
        self.required_role = required_role

    def __call__(self, user: User = Depends(get_current_user)):
        if self._hierarchy.get(user.role, 0) < self._hierarchy.get(self.required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return user

allow_admin = RoleChecker(UserRole.admin)
