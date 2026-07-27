import bcrypt

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
