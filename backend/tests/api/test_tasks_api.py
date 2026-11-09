from datetime import date

from fastapi.testclient import TestClient

from tests.conftest import AuthHeaders
from tests.fakes import RecordingNotifier

URL = "/api/v1/tasks"


def create(client: TestClient, headers: AuthHeaders, **body: object) -> dict[str, object]:
    payload: dict[str, object] = {"title": "Task"}
    payload.update(body)
    res = client.post(URL, json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()  # type: ignore[no-any-return]


def test_crud_happy_path(client: TestClient, owner: tuple[int, AuthHeaders]) -> None:
    user_id, h = owner
    task = create(client, h, title="Write docs", description="Swagger", due_date="2026-12-01")
    assert task["owner_id"] == user_id
    assert task["status"] == "pending"

    tid = task["id"]
    assert client.get(f"{URL}/{tid}", headers=h).json()["title"] == "Write docs"

    res = client.patch(f"{URL}/{tid}", json={"title": "Write better docs"}, headers=h)
    assert res.status_code == 200
    assert res.json()["title"] == "Write better docs"
    assert res.json()["description"] == "Swagger"

    assert client.delete(f"{URL}/{tid}", headers=h).status_code == 204
    assert client.get(f"{URL}/{tid}", headers=h).status_code == 404


def test_create_validation(client: TestClient, owner: tuple[int, AuthHeaders]) -> None:
    _, h = owner
    assert client.post(URL, json={"title": ""}, headers=h).status_code == 422
    assert client.post(URL, json={"title": "x", "status": "nope"}, headers=h).status_code == 422
    assert client.post(URL, json={"title": "   "}, headers=h).status_code == 422
    res = client.post(URL, json={"title": "x", "assignee_id": 999}, headers=h)
    assert res.status_code == 422
    assert "Assignee" in res.json()["detail"]


def test_patch_rejects_null_title_and_can_clear_due_date(
    client: TestClient, owner: tuple[int, AuthHeaders]
) -> None:
    _, h = owner
    tid = create(client, h, due_date="2026-12-01")["id"]
    assert client.patch(f"{URL}/{tid}", json={"title": None}, headers=h).status_code == 422
    assert client.patch(f"{URL}/{tid}", json={"status": None}, headers=h).status_code == 422
    res = client.patch(f"{URL}/{tid}", json={"due_date": None}, headers=h)
    assert res.json()["due_date"] is None


def test_assign_and_complete_flow(
    client: TestClient,
    owner: tuple[int, AuthHeaders],
    other: tuple[int, AuthHeaders],
    notifier: RecordingNotifier,
) -> None:
    _, oh = owner
    other_id, xh = other
    tid = create(client, oh)["id"]

    # Stranger cannot see it yet
    assert client.get(f"{URL}/{tid}", headers=xh).status_code == 404

    res = client.post(f"{URL}/{tid}/assign", json={"assignee_id": other_id}, headers=oh)
    assert res.json()["assignee_id"] == other_id
    assert notifier.assigned == [(tid, other_id)]

    # Assignee sees it but cannot edit or delete it
    assert client.get(f"{URL}/{tid}", headers=xh).status_code == 200
    assert client.patch(f"{URL}/{tid}", json={"title": "x"}, headers=xh).status_code == 403
    assert client.delete(f"{URL}/{tid}", headers=xh).status_code == 403

    # ...but can complete it
    res = client.post(f"{URL}/{tid}/complete", headers=xh)
    assert res.json()["status"] == "completed"
    assert res.json()["completed_at"] is not None
    assert len(notifier.completed) == 1


def test_list_pagination(client: TestClient, owner: tuple[int, AuthHeaders]) -> None:
    _, h = owner
    for i in range(12):
        create(client, h, title=f"T{i}")
    body = client.get(URL, params={"page": 2, "size": 5}, headers=h).json()
    assert body["total"] == 12
    assert body["pages"] == 3
    assert body["page"] == 2
    assert len(body["items"]) == 5
    last = client.get(URL, params={"page": 3, "size": 5}, headers=h).json()
    assert len(last["items"]) == 2


def test_list_rejects_invalid_pagination(
    client: TestClient, owner: tuple[int, AuthHeaders]
) -> None:
    _, h = owner
    assert client.get(URL, params={"page": 0}, headers=h).status_code == 422
    assert client.get(URL, params={"size": 101}, headers=h).status_code == 422


def test_list_filters(client: TestClient, owner: tuple[int, AuthHeaders]) -> None:
    _, h = owner
    create(client, h, title="Jan pending", due_date="2026-01-15")
    create(client, h, title="Feb done", due_date="2026-02-15", status="completed")
    create(client, h, title="Mar progress", due_date="2026-03-15", status="in_progress")
    create(client, h, title="No date")

    def titles(**params: str) -> list[str]:
        items = client.get(URL, params=params, headers=h).json()["items"]
        return sorted(t["title"] for t in items)

    assert titles(status="completed") == ["Feb done"]
    assert titles(due_date_from="2026-02-01") == ["Feb done", "Mar progress"]
    assert titles(due_date_to="2026-02-28") == ["Feb done", "Jan pending"]
    assert titles(status="pending", due_date_to="2026-12-31") == ["Jan pending"]
    assert titles(search="prog") == ["Mar progress"]
    res = client.get(
        URL, params={"due_date_from": "2026-05-01", "due_date_to": "2026-01-01"}, headers=h
    )
    assert res.status_code == 422


def test_list_orders_by_due_date_nulls_last(
    client: TestClient, owner: tuple[int, AuthHeaders]
) -> None:
    _, h = owner
    create(client, h, title="none")
    create(client, h, title="late", due_date=str(date(2026, 5, 1)))
    create(client, h, title="soon", due_date=str(date(2026, 1, 1)))
    items = client.get(URL, headers=h).json()["items"]
    assert [t["title"] for t in items] == ["soon", "late", "none"]


def test_list_only_returns_visible_tasks(
    client: TestClient, owner: tuple[int, AuthHeaders], other: tuple[int, AuthHeaders]
) -> None:
    _, oh = owner
    other_id, xh = other
    create(client, oh, title="private")
    create(client, oh, title="shared", assignee_id=other_id)
    create(client, xh, title="mine")
    items = client.get(URL, headers=xh).json()["items"]
    assert sorted(t["title"] for t in items) == ["mine", "shared"]
    filtered = client.get(URL, params={"assignee_id": other_id}, headers=xh).json()["items"]
    assert [t["title"] for t in filtered] == ["shared"]


def test_users_endpoint_lists_active_users(
    client: TestClient, owner: tuple[int, AuthHeaders], other: tuple[int, AuthHeaders]
) -> None:
    _, h = owner
    emails = [u["email"] for u in client.get("/api/v1/users", headers=h).json()]
    assert sorted(emails) == ["other@test.com", "owner@test.com"]


def test_openapi_docs_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/v1/tasks" in schema["paths"]
