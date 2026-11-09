from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.entities import TaskStatus

T = TypeVar("T")


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Prepare sprint demo"])
    description: str = Field(default="", max_length=5000)
    due_date: date | None = None
    assignee_id: int | None = Field(default=None, gt=0)
    status: TaskStatus = TaskStatus.PENDING


class TaskUpdate(BaseModel):
    """PATCH semantics: only fields present in the body are applied.

    Sending `"due_date": null` clears the due date; omitting it leaves it unchanged.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    due_date: date | None = None
    status: TaskStatus | None = None
    assignee_id: int | None = Field(default=None, gt=0)


class TaskAssign(BaseModel):
    assignee_id: int | None = Field(default=None, gt=0, description="null to unassign")


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TaskStatus
    due_date: date | None
    owner_id: int
    assignee_id: int | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
