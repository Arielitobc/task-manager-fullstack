from __future__ import annotations

from dataclasses import dataclass

from app.application.dto import CreateTaskInput, Page, PageRequest, TaskFilters, UpdateTaskInput
from app.application.ports import NotificationDispatcher, TaskRepository, UserRepository
from app.domain.entities import Task, TaskStatus, User
from app.domain.exceptions import NotFoundError, PermissionDeniedError, ValidationError


@dataclass
class TaskService:
    tasks: TaskRepository
    users: UserRepository
    notifier: NotificationDispatcher

    # --- Queries -------------------------------------------------------------------

    def list_tasks(self, actor: User, filters: TaskFilters, page: PageRequest) -> Page[Task]:
        return self.tasks.list_for_user(self._id(actor), filters, page)

    def get_task(self, actor: User, task_id: int) -> Task:
        task = self.tasks.get_by_id(task_id)
        # 404 instead of 403 for tasks the user cannot see: don't leak existence.
        if not task or not task.is_visible_to(self._id(actor)):
            raise NotFoundError(f"Task {task_id} not found")
        return task

    # --- Commands ------------------------------------------------------------------

    def create_task(self, actor: User, data: CreateTaskInput) -> Task:
        if data.assignee_id is not None:
            self._ensure_assignable(data.assignee_id)
        task = Task(
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            owner_id=self._id(actor),
            assignee_id=data.assignee_id,
        )
        if data.status is not TaskStatus.PENDING:
            task.change_status(data.status)
        created = self.tasks.add(task)
        self._notify_assignment(created, actor)
        return created

    def update_task(self, actor: User, task_id: int, data: UpdateTaskInput) -> Task:
        task = self._get_modifiable(actor, task_id)
        sent = data.fields_set
        previous_assignee = task.assignee_id

        task.update_details(
            title=data.title if "title" in sent else None,
            description=data.description if "description" in sent else None,
            due_date=data.due_date if "due_date" in sent else None,
            clear_due_date="due_date" in sent and data.due_date is None,
        )
        if "status" in sent and data.status is not None and data.status != task.status:
            task.change_status(data.status)
        if "assignee_id" in sent:
            if data.assignee_id is not None:
                self._ensure_assignable(data.assignee_id)
            task.assign_to(data.assignee_id)

        updated = self.tasks.update(task)
        if updated.assignee_id != previous_assignee:
            self._notify_assignment(updated, actor)
        return updated

    def delete_task(self, actor: User, task_id: int) -> None:
        task = self._get_modifiable(actor, task_id)
        self.tasks.delete(self._id_of(task))

    def complete_task(self, actor: User, task_id: int) -> Task:
        # Both owner and assignee may complete a task.
        task = self.get_task(actor, task_id)
        if task.status is TaskStatus.COMPLETED:
            return task
        task.complete()
        updated = self.tasks.update(task)
        if updated.owner_id != self._id(actor):
            self.notifier.task_completed(self._id_of(updated), updated.owner_id)
        return updated

    def assign_task(self, actor: User, task_id: int, assignee_id: int | None) -> Task:
        return self.update_task(
            actor,
            task_id,
            UpdateTaskInput(fields_set=frozenset({"assignee_id"}), assignee_id=assignee_id),
        )

    # --- Helpers -------------------------------------------------------------------

    def _get_modifiable(self, actor: User, task_id: int) -> Task:
        task = self.get_task(actor, task_id)
        if not task.can_be_modified_by(self._id(actor)):
            raise PermissionDeniedError("Only the task owner can modify or delete it")
        return task

    def _ensure_assignable(self, user_id: int) -> None:
        user = self.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValidationError(f"Assignee {user_id} does not exist or is inactive")

    def _notify_assignment(self, task: Task, actor: User) -> None:
        if task.assignee_id is not None and task.assignee_id != actor.id:
            self.notifier.task_assigned(self._id_of(task), task.assignee_id)

    @staticmethod
    def _id(user: User) -> int:
        assert user.id is not None, "persisted user expected"
        return user.id

    @staticmethod
    def _id_of(task: Task) -> int:
        assert task.id is not None, "persisted task expected"
        return task.id
