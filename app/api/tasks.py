from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.client import generate_task_description
from app.auth.dependencies import get_current_user, require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.ai import GenerateDescriptionRequest, GenerateDescriptionResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskStatusUpdate, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to access this task",
)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),  # 401 if no valid token
    db: Session = Depends(get_db),
):
    return task_service.create_task(db, current_user, task_in)


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return task_service.list_tasks(db, current_user)



@router.post(
    "/generate-description",
    response_model=GenerateDescriptionResponse,
    
    dependencies=[Depends(get_current_user)],
)
def generate_description(request: GenerateDescriptionRequest):
    return GenerateDescriptionResponse(
        description=generate_task_description(request.title)
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return task_service.get_task(db, current_user, task_id)
    except task_service.TaskNotFoundError:
        raise _NOT_FOUND
    except task_service.TaskAccessDeniedError:
        raise _FORBIDDEN


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return task_service.update_task(db, current_user, task_id, task_in)
    except task_service.TaskNotFoundError:
        raise _NOT_FOUND
    except task_service.TaskAccessDeniedError:
        raise _FORBIDDEN


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    dependencies=[Depends(require_admin)],  # non-admins get 403 before the body runs
)
def update_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        return task_service.update_task_status(db, task_id, status_in.status)
    except task_service.TaskNotFoundError:
        raise _NOT_FOUND