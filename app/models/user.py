import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.task import Task


class UserRole(str, enum.Enum):
    """Allowed roles. Inheriting from str lets us compare with plain strings."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    # Primary key: unique id for each user, auto-incremented by PostgreSQL.
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    # unique=True: no two users can share an email. index=True: fast lookup at login.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # We store the HASH of the password, never the password itself.
    password_hash: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value)

    # server_default: the database fills this in with the current time on insert.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # onupdate: refreshed automatically whenever the row is updated.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Python-side shortcut: user.tasks gives a list of this user's tasks.
    # If a user is deleted, their tasks are deleted too.
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )