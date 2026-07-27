from fastapi import FastAPI
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.protected import router as protected_router
from app.db.session import engine, Base
# Import models to ensure they are registered on Base.metadata
from app.models.user import User
from app.models.token import RefreshToken

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth System API", description="Complete custom auth system")

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(protected_router, prefix="/api", tags=["Protected"])
