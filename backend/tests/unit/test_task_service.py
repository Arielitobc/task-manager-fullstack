from datetime import date

import pytest

from app.application.dto import CreateTaskInput, PageRequest, TaskFilters, UpdateTaskInput
from app.application.use_cases.tasks import TaskService
from app.domain.entities import TaskStatus, User
from app.domain.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from tests.fakes import InMemoryTaskRepository, InMemoryUserRepository, RecordingNotifier


@pytest.fixture
def users() -> InMemoryUserRepository:
    repo = InMemoryUserRepository()
    for name in ("owner", "other", "stranger"):
        repo.add(User(email=f"{name}@x.com", full_name=name, hashed_password="h"))
    return repo


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def service(users: InMemoryUserRepository, notifier: RecordingNotifier) -> TaskService:
    return TaskService(InMemoryTaskRepository(), users, notifier)


def user(users: InMemoryUserRepository, user_id: int) -> User:
    found = users.get_by_id(user_id)
    assert found
    return found


def test_create_task_sets_owner(service: TaskService, users: InMemoryUserRepository) -> None:
    task = service.create_task(user(users, 1), CreateTaskInput(title="Do it"))
    assert task.id is not None
    assert task.owner_id == 1
    assert task.status is TaskStatus.PENDING


def test_create_with_assignee_notifies(
    service: TaskService, users: InMemoryUserRepository, notifier: RecordingNotifier
) -> None:
    task = service.create_task(user(users, 1), CreateTaskInput(title="Do it", assignee_id=2))
    assert notifier.assigned == [(task.id, 2)]


def test_self_assignment_does_not_notify(
    service: TaskService, users: InMemoryUserRepository, notifier: RecordingNotifier
) -> None:
    service.create_task(user(users, 1), CreateTaskInput(title="Do it", assignee_id=1))
    assert notifier.assigned == []


def test_create_with_unknown_assignee_fails(
    service: TaskService, users: InMemoryUserRepository
) -> None:
    with pytest.raises(ValidationError):
        service.create_task(user(users, 1), CreateTaskInput(title="x", assignee_id=99))


def test_create_completed_task_sets_completed_at(
    service: TaskService, users: InMemoryUserRepository
) -> None:
    task = service.create_task(
        user(users, 1), CreateTaskInput(title="x", status=TaskStatus.COMPLETED)
    )
    assert task.completed_at is not None


def test_stranger_cannot_see_task(service: TaskService, users: InMemoryUserRepository) -> None:
    task = service.create_task(user(users, 1), CreateTaskInput(title="x", assignee_id=2))
    assert task.id is not None
    assert service.get_task(user(users, 2), task.id).id == task.id
    with pytest.raises(NotFoundError):
        service.get_task(user(users, 3), task.id)


def test_partial_update_only_changes_sent_fields(
    service: TaskService, users: InMemoryUserRepository
) -> None:
    owner = user(users, 1)
    task = service.create_task(
        owner, CreateTaskInput(title="x", description="keep", due_date=date(2026, 1, 1))
    )
    assert task.id is not None
    updated = service.update_task(
        owner,
        task.id,
        UpdateTaskInput(
            fields_set=frozenset({"title", "status"}), title="new", status=TaskStatus.IN_PROGRESS
        ),
    )
    assert updated.title == "new"
    assert updated.description == "keep"
    assert updated.due_date == date(2026, 1, 1)
    assert updated.status is TaskStatus.IN_PROGRESS


def test_update_can_clear_due_date(service: TaskService, users: InMemoryUserRepository) -> None:
    owner = user(users, 1)
    task = service.create_task(owner, CreateTaskInput(title="x", due_date=date(2026, 1, 1)))
    assert task.id is not None
    updated = service.update_task(
        owner, task.id, UpdateTaskInput(fields_set=frozenset({"due_date"}), due_date=None)
    )
    assert updated.due_date is None


def test_assignee_cannot_update_or_delete(
    service: TaskService, users: InMemoryUserRepository
) -> None:
    task = service.create_task(user(users, 1), CreateTaskInput(title="x", assignee_id=2))
    assert task.id is not None
    with pytest.raises(PermissionDeniedError):
        service.update_task(
            user(users, 2), task.id, UpdateTaskInput(fields_set=frozenset({"title"}), title="y")
        )
    with pytest.raises(PermissionDeniedError):
        service.delete_task(user(users, 2), task.id)


def test_owner_can_delete(service: TaskService, users: InMemoryUserRepository) -> None:
    owner = user(users, 1)
    task = service.create_task(owner, CreateTaskInput(title="x"))
    assert task.id is not None
    service.delete_task(owner, task.id)
    with pytest.raises(NotFoundError):
        service.get_task(owner, task.id)


def test_assignee_can_complete_and_owner_is_notified(
    service: TaskService, users: InMemoryUserRepository, notifier: RecordingNotifier
) -> None:
    task = service.create_task(user(users, 1), CreateTaskInput(title="x", assignee_id=2))
    assert task.id is not None
    done = service.complete_task(user(users, 2), task.id)
    assert done.status is TaskStatus.COMPLETED
    assert notifier.completed == [(task.id, 1)]
    # Completing twice is idempotent and does not notify again.
    service.complete_task(user(users, 2), task.id)
    assert len(notifier.completed) == 1


def test_reassign_notifies_new_assignee(
    service: TaskService, users: InMemoryUserRepository, notifier: RecordingNotifier
) -> None:
    owner = user(users, 1)
    task = service.create_task(owner, CreateTaskInput(title="x"))
    assert task.id is not None
    service.assign_task(owner, task.id, 2)
    assert notifier.assigned == [(task.id, 2)]
    unassigned = service.assign_task(owner, task.id, None)
    assert unassigned.assignee_id is None


def test_list_filters_by_status_and_due_date(
    service: TaskService, users: InMemoryUserRepository
) -> None:
    owner = user(users, 1)
    service.create_task(owner, CreateTaskInput(title="a", due_date=date(2026, 1, 10)))
    service.create_task(
        owner, CreateTaskInput(title="b", due_date=date(2026, 2, 10), status=TaskStatus.COMPLETED)
    )
    page = service.list_tasks(
        owner,
        TaskFilters(status=TaskStatus.PENDING, due_date_to=date(2026, 1, 31)),
        PageRequest(page=1, size=10),
    )
    assert [t.title for t in page.items] == ["a"]
    assert page.total == 1
    assert page.pages == 1


@pytest.mark.parametrize(("page", "size"), [(0, 10), (1, 0), (1, 101)])
def test_invalid_page_request(page: int, size: int) -> None:
    with pytest.raises(ValueError):
        PageRequest(page=page, size=size)
