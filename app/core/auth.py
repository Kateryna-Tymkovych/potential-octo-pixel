from datetime import datetime, timedelta, timezone
from fastapi import Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.token import RefreshToken
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserRegister
from app.core.security import (
    get_password_hash,
    verify_password,
    create_token,
    decode_token
)
from app.core.config import settings

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not await verify_password(password, user.hashed_password):
        return None
    return user

async def register_user(db: AsyncSession, user_in: UserRegister | UserCreate) -> User:
    hashed_password = await get_password_hash(user_in.password)
    role = getattr(user_in, "role", UserRole.user)
    db_obj = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(db_obj)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    return db_obj

async def issue_tokens(db: AsyncSession, response: Response, user_id: int) -> dict:
    access_token, _ = create_token(data={"sub": str(user_id)}, token_type="access")
    refresh_token, refresh_payload = create_token(data={"sub": str(user_id)}, token_type="refresh")

    # Save refresh token JTI to DB for revocation tracking
    db_refresh_token = RefreshToken(
        jti=refresh_payload["jti"],
        user_id=user_id
    )
    db.add(db_refresh_token)
    await db.commit()

    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

async def rotate_refresh_token(db: AsyncSession, response: Response, refresh_token: str | None) -> dict:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    # Verify JWT validity and get JTI
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        if not jti:
            raise ValueError("Missing jti")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify JTI in DB
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked:
        if db_token and db_token.revoked:
            # Potential reuse attack: revoke all tokens for this user
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == db_token.user_id)
                .values(revoked=True)
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reuse detected",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Rotate: Revoke old token
    db_token.revoked = True

    # Issue new tokens
    return await issue_tokens(db, response, db_token.user_id)

async def revoke_refresh_token(db: AsyncSession, response: Response, refresh_token: str | None):
    if refresh_token:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            jti = payload.get("jti")
            if jti:
                result = await db.execute(
                    select(RefreshToken).where(RefreshToken.jti == jti)
                )
                db_token = result.scalar_one_or_none()
                if db_token:
                    db_token.revoked = True
                    await db.commit()
        except ValueError:
            pass  # Token already invalid/expired

    response.delete_cookie(key="refresh_token", path=settings.AUTH_COOKIE_PATH)

def _set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=settings.AUTH_COOKIE_PATH,
    )
