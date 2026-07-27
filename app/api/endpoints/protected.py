from fastapi import APIRouter, Depends
from app.api.deps import RoleChecker

router = APIRouter()

@router.get("/admin-only", dependencies=[Depends(RoleChecker(["admin"]))])
def admin_route():
    return {"msg": "Hello Admin"}

@router.get("/user-area", dependencies=[Depends(RoleChecker(["admin", "user"]))])
def user_route():
    return {"msg": "Hello User"}
