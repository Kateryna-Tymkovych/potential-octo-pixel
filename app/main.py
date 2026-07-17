from fastapi import FastAPI, Depends
from app.api.v1.api import api_router
from app.core.config import settings
from app.api.deps import RoleChecker
from app.models.user import UserRole, User

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI Auth System"}

@app.get("/test/admin", dependencies=[Depends(RoleChecker(UserRole.ADMIN))])
def test_admin():
    return {"message": "Hello Admin"}

@app.get("/test/user", dependencies=[Depends(RoleChecker(UserRole.USER))])
def test_user():
    return {"message": "Hello User"}

@app.get("/test/guest", dependencies=[Depends(RoleChecker(UserRole.GUEST))])
def test_guest():
    return {"message": "Hello Guest"}
