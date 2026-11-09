"""In-memory adapters used to unit-test use cases without a database."""

from __future__ import annotations

from dataclasses import replace

from app.application.dto import Page, PageRequest, TaskFilters
from app.domain.entities import Task, User
from app.domain.exceptions import AuthenticationError


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._items: dict[int, User] = {}
        self._next_id = 1

    def add(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self._items[user.id] = user
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self._items.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._items.values() if u.email == email), None)

    def list_active(self) -> list[User]:
        return [u for u in self._items.values() if u.is_active]


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._items: dict[int, Task] = {}
        self._next_id = 1

    def add(self, task: Task) -> Task:
        task.id = self._next_id
        self._next_id += 1
        self._items[task.id] = replace(task)
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        task = self._items.get(task_id)
        return replace(task) if task else None

    def update(self, task: Task) -> Task:
        assert task.id is not None
        self._items[task.id] = replace(task)
        return task

    def delete(self, task_id: int) -> None:
        self._items.pop(task_id, None)

    def list_for_user(self, user_id: int, filters: TaskFilters, page: PageRequest) -> Page[Task]:
        items = [t for t in self._items.values() if t.is_visible_to(user_id)]
        if filters.status:
            items = [t for t in items if t.status == filters.status]
        if filters.due_date_from:
            items = [t for t in items if t.due_date and t.due_date >= filters.due_date_from]
        if filters.due_date_to:
            items = [t for t in items if t.due_date and t.due_date <= filters.due_date_to]
        total = len(items)
        return Page(items[page.offset : page.offset + page.size], total, page.page, page.size)


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed::{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed::{password}"


class FakeTokenService:
    def create_access_token(self, subject: str) -> str:
        return f"token::{subject}"

    def decode_subject(self, token: str) -> str:
        if not token.startswith("token::"):
            raise AuthenticationError("bad token")
        return token.removeprefix("token::")


class RecordingNotifier:
    def __init__(self) -> None:
        self.assigned: list[tuple[int, int]] = []
        self.completed: list[tuple[int, int]] = []

    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        self.assigned.append((task_id, assignee_id))

    def task_completed(self, task_id: int, owner_id: int) -> None:
        self.completed.append((task_id, owner_id))
