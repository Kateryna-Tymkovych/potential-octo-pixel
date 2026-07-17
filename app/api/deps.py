from typing import Generator, List
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import TokenType
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.token import BlacklistedToken
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

def verify_token(db: Session, token: str, expected_type: TokenType) -> TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    if token_data.type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check blacklist
    blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.token_jti == token_data.jti).first()
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    return token_data

def get_token_payload(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> TokenPayload:
    return verify_token(db, token, TokenType.ACCESS)

def get_current_user(
    db: Session = Depends(get_db),
    token_data: TokenPayload = Depends(get_token_payload)
) -> User:
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

role_hierarchy = {
    UserRole.ADMIN: 3,
    UserRole.USER: 2,
    UserRole.GUEST: 1
}

class RoleChecker:
    def __init__(self, min_role: UserRole):
        self.min_role = min_role

    def __call__(self, user: User = Depends(get_current_user)):
        if role_hierarchy.get(user.role, 0) < role_hierarchy.get(self.min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return user
