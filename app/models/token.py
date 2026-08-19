from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from app.db.session import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token = Column(String, primary_key=True, index=True)
    revoked_at = Column(DateTime, default=get_utc_now)
