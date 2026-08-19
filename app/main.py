from fastapi import FastAPI, Depends
from app.api.endpoints import auth
from app.db.session import engine, Base
from app.api.deps import RoleChecker
from app.schemas.user import UserOut

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Auth System")

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/guest-only", response_model=UserOut)
def guest_only(current_user=Depends(RoleChecker(["guest", "user", "admin"]))):
    return current_user

@app.get("/user-only", response_model=UserOut)
def user_only(current_user=Depends(RoleChecker(["user", "admin"]))):
    return current_user

@app.get("/admin-only", response_model=UserOut)
def admin_only(current_user=Depends(RoleChecker(["admin"]))):
    return current_user

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auth System API"}
