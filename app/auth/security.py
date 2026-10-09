from datetime import datetime, timedelta, timezone

import bcrypt
import jwt  

from app.config import settings



def hash_password(plain_password: str) -> str:
    """Turn a plain password into a salted bcrypt hash (safe to store)."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a typed password against a stored hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        # Malformed hash or too-long password: treat as "does not match".
        return False




def create_access_token(user_id: int) -> str:
    """Build and sign a JWT for this user."""
    now = datetime.now(timezone.utc)
    payload = {
        # "sub" must be a string in current PyJWT versions.
        # We store ONLY the user id. Role is NOT put in the token:
        # it is always re-read from the database.
        "sub": str(user_id),
        "iat": now,  # issued at
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),  # expiry
    }
    # encode() creates header + payload, then signs them with our secret key.
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verify the signature and expiry, and return the payload.

    Raises jwt.InvalidTokenError (or its subclass ExpiredSignatureError) if the
    token is tampered, malformed, or expired. The caller decides what to do;
    this function stays free of any HTTP knowledge.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        # Reject tokens that lack an expiry or a subject.
        options={"require": ["exp", "sub"]},
    )