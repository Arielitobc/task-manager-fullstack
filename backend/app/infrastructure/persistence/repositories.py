"""SQLAlchemy implementations of the repository ports.

ORM models never leave this module: everything is mapped to/from domain entities.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.application.dto import Page, PageRequest, TaskFilters
from app.domain.entities import Task, User
from app.infrastructure.persistence.models import TaskModel, UserModel


def _to_user(m: UserModel) -> User:
    return User(
        id=m.id,
        email=m.email,
        full_name=m.full_name,
        hashed_password=m.hashed_password,
        is_active=m.is_active,
        created_at=m.created_at,
    )


def _to_task(m: TaskModel) -> Task:
    return Task(
        id=m.id,
        title=m.title,
        description=m.description,
        status=m.status,
        due_date=m.due_date,
        owner_id=m.owner_id,
        assignee_id=m.assignee_id,
        completed_at=m.completed_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _apply_task(m: TaskModel, t: Task) -> None:
    m.title = t.title
    m.description = t.description
    m.status = t.status
    m.due_date = t.due_date
    m.owner_id = t.owner_id
    m.assignee_id = t.assignee_id
    m.completed_at = t.completed_at
    m.created_at = t.created_at
    m.updated_at = t.updated_at


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            full_name=user.full_name,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return _to_user(model)

    def get_by_id(self, user_id: int) -> User | None:
        model = self.session.get(UserModel, user_id)
        return _to_user(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email))
        return _to_user(model) if model else None

    def list_active(self) -> list[User]:
        rows = self.session.scalars(
            select(UserModel).where(UserModel.is_active.is_(True)).order_by(UserModel.full_name)
        )
        return [_to_user(m) for m in rows]


class SqlAlchemyTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, task: Task) -> Task:
        model = TaskModel()
        _apply_task(model, task)
        self.session.add(model)
        self.session.flush()
        return _to_task(model)

    def get_by_id(self, task_id: int) -> Task | None:
        model = self.session.get(TaskModel, task_id)
        return _to_task(model) if model else None

    def update(self, task: Task) -> Task:
        model = self.session.get(TaskModel, task.id)
        if model is None:  # pragma: no cover - guarded by the use case
            raise LookupError(f"Task {task.id} not found")
        _apply_task(model, task)
        self.session.flush()
        return _to_task(model)

    def delete(self, task_id: int) -> None:
        model = self.session.get(TaskModel, task_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def list_for_user(self, user_id: int, filters: TaskFilters, page: PageRequest) -> Page[Task]:
        query = self._filtered(user_id, filters)
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = self.session.scalars(
            query.order_by(TaskModel.due_date.asc().nulls_last(), TaskModel.id.desc())
            .offset(page.offset)
            .limit(page.size)
        )
        return Page([_to_task(m) for m in rows], total, page.page, page.size)

    @staticmethod
    def _filtered(user_id: int, f: TaskFilters) -> Select[Any]:
        query = select(TaskModel).where(
            or_(TaskModel.owner_id == user_id, TaskModel.assignee_id == user_id)
        )
        if f.status is not None:
            query = query.where(TaskModel.status == f.status)
        if f.due_date_from is not None:
            query = query.where(TaskModel.due_date >= f.due_date_from)
        if f.due_date_to is not None:
            query = query.where(TaskModel.due_date <= f.due_date_to)
        if f.assignee_id is not None:
            query = query.where(TaskModel.assignee_id == f.assignee_id)
        if f.search:
            pattern = f"%{f.search.strip()}%"
            query = query.where(
                or_(TaskModel.title.ilike(pattern), TaskModel.description.ilike(pattern))
            )
        return query
