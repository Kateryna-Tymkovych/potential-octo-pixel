from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from sqlalchemy.orm import Session

from src.app.api import deps
from src.app.core import security
from src.app.core.config import settings
from src.app.db.models import User, RefreshToken
from src.app.schemas.user import UserCreate, UserOut
from src.app.schemas.token import Token

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    response: Response, user_in: UserCreate, db: Session = Depends(deps.get_db)
):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not security.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    now = datetime.now(timezone.utc)
    access_token = security.create_access_token(subject=user.id)
    refresh_token_str = security.create_refresh_token(subject=user.id)

    # Store refresh token in DB
    refresh_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    db_obj = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=now.replace(tzinfo=None) + timedelta(days=refresh_expire_days),
    )
    db.add(db_obj)
    db.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=refresh_expire_days * 24 * 60 * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(deps.get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    now = datetime.now(timezone.utc)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.revoked == False
    ).first()

    if not db_token or db_token.expires_at < now.replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotate Refresh Token
    db_token.revoked = True

    new_refresh_token_str = security.create_refresh_token(subject=db_token.user_id)
    refresh_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    new_db_token = RefreshToken(
        token=new_refresh_token_str,
        user_id=db_token.user_id,
        expires_at=now.replace(tzinfo=None) + timedelta(days=refresh_expire_days),
    )
    db.add(new_db_token)
    db.commit()

    access_token = security.create_access_token(subject=db_token.user_id)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_str,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=refresh_expire_days * 24 * 60 * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(deps.get_db),
):
    if refresh_token:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
        if db_token:
            db_token.revoked = True
            db.commit()

    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}
