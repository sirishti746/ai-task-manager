from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    """Data the client sends to register. There is NO role field on purpose:
    clients can never choose their own role (prevents privilege escalation)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value

class UserLogin(BaseModel):
    """Data the client sends to log in (JSON body)."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class TokenResponse(BaseModel):
    """What login returns. 'bearer' tells the client how to send the token."""

    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """Data we send back. Notice: no password and no password_hash."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime