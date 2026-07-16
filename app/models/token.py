from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
