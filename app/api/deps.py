from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def raise_credentials_exception() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    token: str = Depends(reusable_oauth2),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise_credentials_exception()

    user_id: str = payload.get("sub")
    if user_id is None or not user_id.isdigit():
        raise_credentials_exception()

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise_credentials_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
