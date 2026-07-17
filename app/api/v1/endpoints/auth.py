from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.token import BlacklistedToken
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token, TokenPayload
from app.api import deps
import jwt

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Any:
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    db_obj = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

def set_refresh_cookie(response: Response, refresh_token: str, expires_delta: timedelta):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(expires_delta.total_seconds())
    )

def blacklist_token_payload(db: Session, token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload["jti"]
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
        if not db.query(BlacklistedToken).filter(BlacklistedToken.token_jti == jti).first():
            db.add(BlacklistedToken(token_jti=jti, expires_at=exp))
    except Exception:
        pass

def create_tokens(user_id: int):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = security.create_token(
        user_id, expires_delta=access_token_expires, token_type=security.TokenType.ACCESS
    )
    refresh_token = security.create_token(
        user_id, expires_delta=refresh_token_expires, token_type=security.TokenType.REFRESH
    )
    return access_token, refresh_token, refresh_token_expires

@router.post("/login", response_model=Token)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not security.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token, refresh_token, refresh_expires = create_tokens(user.id)
    set_refresh_cookie(response, refresh_token, refresh_expires)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> Any:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token_data = deps.verify_token(db, refresh_token, security.TokenType.REFRESH)
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Blacklist old refresh token (rotation)
    blacklist_token_payload(db, refresh_token)

    access_token, refresh_token, refresh_expires = create_tokens(user.id)
    db.commit()

    set_refresh_cookie(response, refresh_token, refresh_expires)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    token: str = Depends(deps.reusable_oauth2)
) -> Any:
    # Blacklist access token
    blacklist_token_payload(db, token)

    # Blacklist refresh token if present
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        blacklist_token_payload(db, refresh_token)

    db.commit()
    response.delete_cookie("refresh_token")
    return {"msg": "Successfully logged out"}
