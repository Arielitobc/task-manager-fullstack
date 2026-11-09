"""Data transfer objects shared between use cases and adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import ceil
from typing import Generic, TypeVar

from app.domain.entities import TaskStatus

T = TypeVar("T")

MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageRequest:
    page: int = 1
    size: int = 10

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= self.size <= MAX_PAGE_SIZE:
            raise ValueError(f"size must be between 1 and {MAX_PAGE_SIZE}")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.total else 0


@dataclass(frozen=True)
class TaskFilters:
    status: TaskStatus | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None
    assignee_id: int | None = None
    search: str | None = None


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    description: str = ""
    due_date: date | None = None
    assignee_id: int | None = None
    status: TaskStatus = TaskStatus.PENDING


@dataclass(frozen=True)
class UpdateTaskInput:
    """Partial update. `fields_set` tells which attributes were explicitly sent."""

    fields_set: frozenset[str]
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    status: TaskStatus | None = None
    assignee_id: int | None = None
