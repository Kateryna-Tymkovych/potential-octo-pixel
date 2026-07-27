from fastapi import FastAPI
from app.api.endpoints.auth import router as auth_router
from app.db.session import engine, Base
# Import models to ensure they are registered on Base.metadata
from app.models.user import User
from app.models.token import RefreshToken

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
