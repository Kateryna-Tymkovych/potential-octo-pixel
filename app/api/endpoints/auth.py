from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.api import deps
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.services import auth_service

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    return auth_service.register_user(db, user_in)

@router.post("/login", response_model=Token)
def login(response: Response, user_in: UserCreate, db: Session = Depends(deps.get_db)):
    user = auth_service.authenticate(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token, refresh_token = auth_service.create_tokens(user)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh(request: Request, response: Response, db: Session = Depends(deps.get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    access_token, new_refresh_token = auth_service.refresh_token_rotation(db, refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(deps.get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        auth_service.revoke_token(db, refresh_token)

    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}
