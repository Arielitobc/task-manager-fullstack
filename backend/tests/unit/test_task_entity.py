import pytest

from app.domain.entities import Task, TaskStatus
from app.domain.exceptions import ValidationError


def make_task(**kwargs: object) -> Task:
    defaults: dict[str, object] = {"title": "Write tests", "owner_id": 1}
    defaults.update(kwargs)
    return Task(**defaults)  # type: ignore[arg-type]


def test_title_is_trimmed() -> None:
    assert make_task(title="  Hello  ").title == "Hello"


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_invalid_title_is_rejected(title: str) -> None:
    with pytest.raises(ValidationError):
        make_task(title=title)


def test_complete_sets_status_and_timestamp() -> None:
    task = make_task()
    task.complete()
    assert task.status is TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_reopening_clears_completed_at() -> None:
    task = make_task()
    task.complete()
    task.change_status(TaskStatus.IN_PROGRESS)
    assert task.completed_at is None


def test_visibility_and_ownership_rules() -> None:
    task = make_task(owner_id=1, assignee_id=2)
    assert task.is_visible_to(1)
    assert task.is_visible_to(2)
    assert not task.is_visible_to(3)
    assert task.can_be_modified_by(1)
    assert not task.can_be_modified_by(2)
