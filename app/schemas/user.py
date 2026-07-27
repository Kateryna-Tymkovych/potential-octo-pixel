import re
from pydantic import BaseModel, field_validator, ConfigDict

class UserBase(BaseModel):
    email: str
    role: str = "user"
    is_active: bool = True

class UserCreate(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format')
        return v

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Alias to UserSchema as mentioned in endpoint templates
UserSchema = UserOut
