from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, TaskServiceDep
from app.api.schemas import (
    ErrorResponse,
    PageResponse,
    TaskAssign,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.application.dto import CreateTaskInput, PageRequest, TaskFilters, UpdateTaskInput
from app.domain.entities import TaskStatus

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)


@router.get("", response_model=PageResponse[TaskRead])
def list_tasks(
    user: CurrentUser,
    service: TaskServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    status_: Annotated[TaskStatus | None, Query(alias="status")] = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    assignee_id: Annotated[int | None, Query(gt=0)] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
) -> PageResponse[TaskRead]:
    """Tasks the current user owns or is assigned to, ordered by due date."""
    if due_date_from and due_date_to and due_date_from > due_date_to:
        raise HTTPException(422, "due_date_from must be before due_date_to")
    result = service.list_tasks(
        user,
        TaskFilters(
            status=status_,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            assignee_id=assignee_id,
            search=search or None,
        ),
        PageRequest(page=page, size=size),
    )
    return PageResponse[TaskRead](
        items=[TaskRead.model_validate(t) for t in result.items],
        total=result.total,
        page=result.page,
        size=result.size,
        pages=result.pages,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(body: TaskCreate, user: CurrentUser, service: TaskServiceDep) -> TaskRead:
    task = service.create_task(user, CreateTaskInput(**body.model_dump()))
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, user: CurrentUser, service: TaskServiceDep) -> TaskRead:
    return TaskRead.model_validate(service.get_task(user, task_id))


@router.patch("/{task_id}", response_model=TaskRead, responses={403: {"model": ErrorResponse}})
def update_task(
    task_id: int, body: TaskUpdate, user: CurrentUser, service: TaskServiceDep
) -> TaskRead:
    sent = frozenset(body.model_fields_set)
    if "title" in sent and body.title is None:
        raise HTTPException(422, "title cannot be null")
    if "status" in sent and body.status is None:
        raise HTTPException(422, "status cannot be null")
    data = UpdateTaskInput(fields_set=sent, **body.model_dump())
    return TaskRead.model_validate(service.update_task(user, task_id, data))


@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses={403: {"model": ErrorResponse}}
)
def delete_task(task_id: int, user: CurrentUser, service: TaskServiceDep) -> Response:
    service.delete_task(user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: int, user: CurrentUser, service: TaskServiceDep) -> TaskRead:
    """Owner or assignee can mark a task as completed (idempotent)."""
    return TaskRead.model_validate(service.complete_task(user, task_id))


@router.post(
    "/{task_id}/assign", response_model=TaskRead, responses={403: {"model": ErrorResponse}}
)
def assign_task(
    task_id: int, body: TaskAssign, user: CurrentUser, service: TaskServiceDep
) -> TaskRead:
    return TaskRead.model_validate(service.assign_task(user, task_id, body.assignee_id))
