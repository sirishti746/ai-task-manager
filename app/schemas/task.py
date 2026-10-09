from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    """Body of POST /api/tasks. There is NO user_id and NO status field:
    the owner comes from the JWT, and a new task is always 'Pending'."""

    # Strip spaces around text, so a title of "   " becomes "" and fails min_length.
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)  # max matches String(200) in the DB
    description: Optional[str] = Field(default=None, max_length=5000)


class TaskUpdate(BaseModel):
    """Body of PUT /api/tasks/{id}. Only title and description can change.
    Any other field a client sends (like 'status' or 'user_id') is ignored,
    because it is not declared here."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Both optional: send only what you want to change.
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("title")
    @classmethod
    def title_cannot_be_null(cls, value):
        # Omitting title is fine (keeps the old one), but sending "title": null
        # would try to write NULL into a NOT NULL column. Reject it as a 422.
        if value is None:
            raise ValueError("title cannot be null")
        return value


class TaskStatusUpdate(BaseModel):
    """Body of PATCH /api/tasks/{id}/status.
    Typing the field as the TaskStatus enum makes Pydantic accept only the four
    allowed strings; anything else returns 422 automatically."""

    status: TaskStatus


class TaskResponse(BaseModel):
    """What we return for a task."""

    # from_attributes=True lets Pydantic read a SQLAlchemy Task object directly.
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime