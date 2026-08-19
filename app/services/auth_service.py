from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.token import RevokedToken
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token

def register_user(db: Session, user_in: UserCreate) -> User:
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    db_obj = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role="user",
        is_active=True
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_tokens(user: User):
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role})
    return access_token, refresh_token

def revoke_token(db: Session, token: str):
    revoked_token = RevokedToken(token=token)
    db.add(revoked_token)
    db.commit()

def refresh_token_rotation(db: Session, refresh_token: str):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is revoked
    db_revoked = db.query(RevokedToken).filter(RevokedToken.token == refresh_token).first()
    if db_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Revoke old token
    revoke_token(db, refresh_token)

    # Issue new pair
    return create_tokens(user)
