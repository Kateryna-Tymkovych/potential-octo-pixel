from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from app.api.endpoints.auth import router as auth_router
from app.api.deps import RoleChecker
from app.models.user import User
from app.models.base import Base
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="FastAPI Authentication System", lifespan=lifespan)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Authentication System"}

@app.get("/admin-only")
async def admin_only(current_user: User = Depends(RoleChecker(["admin"]))):
    return {"message": "Welcome Admin!", "user": current_user.email}

@app.get("/user-only")
async def user_only(current_user: User = Depends(RoleChecker(["user", "admin"]))):
    return {"message": "Welcome User!", "user": current_user.email}
