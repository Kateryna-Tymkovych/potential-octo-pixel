import enum
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from passlib.context import CryptContext
import uuid
from app.core.config import settings

class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(subject: Any, expires_delta: timedelta, token_type: TokenType) -> str:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload = {
        "exp": expire,
        "iat": now,
        "sub": str(subject),
        "type": token_type.value,
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
