import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from app.core.config import settings

class DirectBcryptContext:
    """
    A compatible wrapper that behaves like passlib's CryptContext
    but uses the modern bcrypt library directly under the hood.
    This bypasses the unmaintained Passlib/bcrypt compatibility bugs on Python 3.13.
    """
    def __init__(self, schemes=None, deprecated=None):
        pass

    def hash(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify(self, secret: str, hash: str) -> bool:
        try:
            return bcrypt.checkpw(secret.encode('utf-8'), hash.encode('utf-8'))
        except Exception:
            return False

# Maintain exact API matching Step 6 requirements
pwd_context = DirectBcryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(data, "access", delta)

def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(data, "refresh", delta)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
