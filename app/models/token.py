from sqlalchemy import Column, String, DateTime
from app.db.base_class import Base

class BlacklistedToken(Base):
    token_jti = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
