"""Domain entities. Plain dataclasses: no ORM, no web framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum

from app.domain.exceptions import ValidationError


def utcnow() -> datetime:
    return datetime.now(UTC)


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class User:
    email: str
    full_name: str
    hashed_password: str
    id: int | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=utcnow)


TITLE_MAX_LENGTH = 200


@dataclass
class Task:
    title: str
    owner_id: int
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    due_date: date | None = None
    assignee_id: int | None = None
    id: int | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        self.title = self._validate_title(self.title)

    @staticmethod
    def _validate_title(title: str) -> str:
        cleaned = title.strip()
        if not cleaned:
            raise ValidationError("Task title cannot be empty")
        if len(cleaned) > TITLE_MAX_LENGTH:
            raise ValidationError(f"Task title cannot exceed {TITLE_MAX_LENGTH} characters")
        return cleaned

    # --- Business rules -------------------------------------------------------------

    def is_visible_to(self, user_id: int) -> bool:
        return user_id in (self.owner_id, self.assignee_id)

    def can_be_modified_by(self, user_id: int) -> bool:
        return user_id == self.owner_id

    def change_status(self, status: TaskStatus) -> None:
        self.status = status
        self.completed_at = utcnow() if status is TaskStatus.COMPLETED else None
        self._touch()

    def complete(self) -> None:
        self.change_status(TaskStatus.COMPLETED)

    def assign_to(self, user_id: int | None) -> None:
        self.assignee_id = user_id
        self._touch()

    def update_details(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        due_date: date | None = None,
        clear_due_date: bool = False,
    ) -> None:
        if title is not None:
            self.title = self._validate_title(title)
        if description is not None:
            self.description = description
        if clear_due_date:
            self.due_date = None
        elif due_date is not None:
            self.due_date = due_date
        self._touch()

    def _touch(self) -> None:
        self.updated_at = utcnow()
