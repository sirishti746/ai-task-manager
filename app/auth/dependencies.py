from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database.session import get_db
from app.models.user import User, UserRole
from app.services import user_service

# Reads "Authorization: Bearer <token>". auto_error=False: if the header is
# missing we get None and raise our own 401 (consistent behavior).
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    """Build a 401. The WWW-Authenticate header tells clients which scheme to use."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Identify who is calling. Used by every protected route."""
    # 1. No Authorization header (or not "Bearer ...") -> 401
    if credentials is None:
        raise _unauthorized("Not authenticated")

    # 2. Verify signature and expiry. Any failure -> 401.
    #    ExpiredSignatureError is a subclass of InvalidTokenError, so one
    #    except covers expired, tampered and malformed tokens.
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid or expired token")

    # 3. "sub" holds the user id as a string; turn it back into an int.
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise _unauthorized("Invalid token")

    # 4. Load the user from the DATABASE. This is where the role comes from,
    #    so it is never stale. If the user was deleted, the token is useless.
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise _unauthorized("User no longer exists")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow only admins. Chains on get_current_user, so an unauthenticated
    caller gets 401 first, and a logged-in non-admin gets 403."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user