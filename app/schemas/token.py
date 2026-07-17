from pydantic import BaseModel
from typing import Optional
from app.core.security import TokenType

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = TokenType.ACCESS

class TokenPayload(BaseModel):
    sub: str
    type: TokenType
    jti: str
