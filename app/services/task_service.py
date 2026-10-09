from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.schemas.task import TaskCreate, TaskUpdate


class TaskNotFoundError(Exception):
    """No task with this id exists. The API layer turns it into a 404."""


class TaskAccessDeniedError(Exception):
    """The task exists but belongs to someone else. The API layer turns it into a 403."""


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN.value


def _get_task_or_raise(db: Session, task_id: int) -> Task:
    # db.get() looks up by primary key and returns None if there is no such row.
    task = db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundError()
    return task


def _ensure_can_access(user: User, task: Task) -> None:
    """The ownership rule, written once: admins may touch any task,
    everyone else only their own."""
    if not _is_admin(user) and task.user_id != user.id:
        raise TaskAccessDeniedError()


def create_task(db: Session, user: User, task_in: TaskCreate) -> Task:
    task = Task(
        user_id=user.id,  # owner comes from the authenticated user, never from the request
        title=task_in.title,
        description=task_in.description,
        # status is not set: the model default "Pending" applies
    )
    db.add(task)
    db.commit()
    db.refresh(task)  # reload database-generated values (id, created_at, updated_at)
    return task


def list_tasks(db: Session, user: User) -> list[Task]:
    stmt = select(Task).order_by(Task.created_at.desc(), Task.id.desc())  # newest first
    if not _is_admin(user):
        # Regular users: the filter is part of the query itself,
        # so other people's rows are never even loaded.
        stmt = stmt.where(Task.user_id == user.id)
    return list(db.execute(stmt).scalars().all())


def get_task(db: Session, user: User, task_id: int) -> Task:
    task = _get_task_or_raise(db, task_id)  # 404 if missing
    _ensure_can_access(user, task)          # 403 if it is someone else's
    return task


def update_task(db: Session, user: User, task_id: int, task_in: TaskUpdate) -> Task:
    task = get_task(db, user, task_id)  # same 404 / 403 checks as viewing

    # exclude_unset=True: only fields the client actually sent.
    # TaskUpdate declares only title and description, so no other column can be changed.
    for field, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: int, new_status: TaskStatus) -> Task:
    # No ownership check: the route already restricts this to admins,
    # and admins may change any task's status.
    task = _get_task_or_raise(db, task_id)
    task.status = new_status.value  # store the plain string, e.g. "In Progress"
    db.commit()
    db.refresh(task)
    return task