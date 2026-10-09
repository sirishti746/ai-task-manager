from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

# A throwaway hash, computed once at startup. If the email doesn't exist we
# still run a password check against this, so "unknown email" takes about as
# long as "wrong password" and an attacker can't tell them apart by timing.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


class EmailAlreadyRegisteredError(Exception):
    """Raised when registering an email that already exists.
    The service knows nothing about HTTP, so it raises a plain Python
    exception. The API layer translates it into a 409 response."""


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    # Emails are stored lowercase, so "A@x.com" and "a@x.com" are the same user.
    stmt = select(User).where(User.email == email.lower())
    return db.execute(stmt).scalar_one_or_none()  # a User, or None if not found


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    # db.get() looks up by primary key; returns None if there is no such row.
    return db.get(User, user_id)


def create_user(db: Session, user_in: UserCreate) -> User:
    # Friendly check first: gives a clear error in the normal case.
    if get_user_by_email(db, user_in.email) is not None:
        raise EmailAlreadyRegisteredError()

    user = User(
        name=user_in.name,
        email=user_in.email.lower(),
        password_hash=hash_password(user_in.password),  # never store the plain password
        role=UserRole.USER.value,  # registration ALWAYS creates a regular user
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Safety net for two simultaneous registrations of the same email:
        # the UNIQUE constraint rejects the second one.
        db.rollback()
        raise EmailAlreadyRegisteredError()

    db.refresh(user)  # reload database-generated values (id, created_at)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return the user if email + password are correct, otherwise None.
    We return None for BOTH "no such email" and "wrong password" on purpose,
    so the caller can't (and the client can't) tell which one it was."""
    user = get_user_by_email(db, email)
    if user is None:
        verify_password(password, _DUMMY_HASH)  # burn the same time, ignore result
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user