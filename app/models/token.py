from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.db.session import Base

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token = Column(String, primary_key=True, index=True)
    revoked_at = Column(DateTime, default=datetime.utcnow)
