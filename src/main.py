from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from src.app.api.endpoints import auth
from src.app.api import deps
from src.app.db.session import engine, Base
from src.app.schemas.user import UserOut

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="FastAPI Auth System", lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/me", response_model=UserOut)
def read_users_me(current_user=Depends(deps.get_current_user)):
    return current_user


@app.get("/admin-only")
def read_admin_only(admin_user=Depends(deps.RoleChecker(["admin"]))):
    return {"message": "Hello Admin", "admin_email": admin_user.email}
