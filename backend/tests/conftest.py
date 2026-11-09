import os

# Configure before the app (and its module-level limiter / Celery app) is imported.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes!")

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.infrastructure.persistence.database import Base  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.fakes import RecordingNotifier  # noqa: E402

PASSWORD = "Secret123!"


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def app(notifier: RecordingNotifier) -> Iterator[FastAPI]:
    application = create_app(Settings(database_url="sqlite://"))
    application.state.notifier = notifier
    Base.metadata.create_all(application.state.engine)
    yield application
    Base.metadata.drop_all(application.state.engine)
    application.state.engine.dispose()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


AuthHeaders = dict[str, str]


@pytest.fixture
def register_and_login(client: TestClient) -> Callable[[str], tuple[int, AuthHeaders]]:
    def _make(email: str) -> tuple[int, AuthHeaders]:
        res = client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": email.split("@")[0], "password": PASSWORD},
        )
        assert res.status_code == 201, res.text
        token = client.post(
            "/api/v1/auth/login", data={"username": email, "password": PASSWORD}
        ).json()["access_token"]
        return res.json()["id"], {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def owner(register_and_login: Callable[[str], tuple[int, AuthHeaders]]) -> tuple[int, AuthHeaders]:
    return register_and_login("owner@test.com")


@pytest.fixture
def other(register_and_login: Callable[[str], tuple[int, AuthHeaders]]) -> tuple[int, AuthHeaders]:
    return register_and_login("other@test.com")
