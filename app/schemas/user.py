from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Data the client sends to register. There is NO role field on purpose:
    clients can never choose their own role (prevents privilege escalation)."""

    # Strip spaces around the name, so "   " becomes "" and fails min_length.
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr  # validates email format (uses the email-validator library)
    # bcrypt only uses the first 72 BYTES, so we cap the length.
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # max_length counts characters, but bcrypt's limit is in bytes.
        # Non-English characters take more than 1 byte, so check bytes too.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value


class UserLogin(BaseModel):
    """Data the client sends to log in (JSON body)."""

    email: EmailStr
    # No min-length rule here: login should simply say "invalid" for a wrong
    # password, not reveal our password policy. max_length blocks huge inputs.
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """What login returns. 'bearer' tells the client how to send the token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Data we send back. Notice: no password and no password_hash."""

    # from_attributes=True lets Pydantic read fields from a SQLAlchemy object
    # (user.id, user.name, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime