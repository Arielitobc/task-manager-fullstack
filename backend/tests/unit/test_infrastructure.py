from unittest.mock import patch

import pytest

from app.domain.exceptions import AuthenticationError
from app.infrastructure.celery_app import (
    CeleryNotificationDispatcher,
    notify_task_assigned,
    notify_task_completed,
)
from app.infrastructure.security import BcryptPasswordHasher, JwtTokenService


def test_bcrypt_hash_and_verify() -> None:
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("Secret123!")
    assert hashed != "Secret123!"
    assert hasher.verify("Secret123!", hashed)
    assert not hasher.verify("wrong", hashed)
    assert not hasher.verify("x", "not-a-bcrypt-hash")


def test_bcrypt_handles_passwords_longer_than_72_bytes() -> None:
    hasher = BcryptPasswordHasher()
    long_pw = "ñ" * 100
    assert hasher.verify(long_pw, hasher.hash(long_pw))


def test_jwt_round_trip_and_wrong_type() -> None:
    svc = JwtTokenService("k" * 32, "HS256", 5)
    assert svc.decode_subject(svc.create_access_token("42")) == "42"
    import jwt

    refresh_like = jwt.encode({"sub": "1", "exp": 9999999999, "type": "refresh"}, "k" * 32)
    with pytest.raises(AuthenticationError):
        svc.decode_subject(refresh_like)


def test_celery_jobs_run_eagerly() -> None:
    assert notify_task_assigned.delay(1, 2).get() == "Task 1 was assigned to user 2"
    assert "owner 3" in notify_task_completed.delay(1, 3).get()


def test_dispatcher_swallows_broker_errors() -> None:
    dispatcher = CeleryNotificationDispatcher()
    with patch.object(notify_task_assigned, "apply_async", side_effect=ConnectionError("down")):
        dispatcher.task_assigned(1, 2)  # must not raise
    with patch.object(notify_task_completed, "apply_async") as apply_async:
        dispatcher.task_completed(1, 3)
        apply_async.assert_called_once_with(args=(1, 3), retry=False)
