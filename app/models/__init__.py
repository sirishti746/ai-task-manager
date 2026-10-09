# Importing the models here means "import app.models" registers ALL tables
# on Base.metadata. Alembic needs this to see them for autogenerate.
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus

__all__ = ["User", "UserRole", "Task", "TaskStatus"]