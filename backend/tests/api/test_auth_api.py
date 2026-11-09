from fastapi.testclient import TestClient

from app.core.rate_limit import limiter
from app.infrastructure.security import JwtTokenService
from tests.conftest import PASSWORD, AuthHeaders

URL = "/api/v1/auth"


def test_register_login_and_me(client: TestClient, owner: tuple[int, AuthHeaders]) -> None:
    user_id, headers = owner
    res = client.get(f"{URL}/me", headers=headers)
    assert res.status_code == 200
    assert res.json() == {"id": user_id, "email": "owner@test.com", "full_name": "owner"}


def test_password_is_never_returned(client: TestClient) -> None:
    res = client.post(
        f"{URL}/register", json={"email": "a@test.com", "full_name": "A", "password": PASSWORD}
    )
    assert "password" not in res.text


def test_register_duplicate_email_returns_409(
    client: TestClient, owner: tuple[int, AuthHeaders]
) -> None:
    res = client.post(
        f"{URL}/register",
        json={"email": "OWNER@test.com", "full_name": "x", "password": PASSWORD},
    )
    assert res.status_code == 409


def test_register_validates_payload(client: TestClient) -> None:
    res = client.post(f"{URL}/register", json={"email": "bad", "full_name": "", "password": "1"})
    assert res.status_code == 422


def test_login_wrong_password_returns_401(
    client: TestClient, owner: tuple[int, AuthHeaders]
) -> None:
    res = client.post(f"{URL}/login", data={"username": "owner@test.com", "password": "nope"})
    assert res.status_code == 401
    assert res.headers["WWW-Authenticate"] == "Bearer"


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    assert client.get("/api/v1/tasks").status_code == 401


def test_invalid_and_expired_tokens_are_rejected(client: TestClient) -> None:
    expired = JwtTokenService("test-secret-key-with-at-least-32-bytes!", "HS256", -1)
    for token in ("not-a-jwt", expired.create_access_token("1")):
        res = client.get(f"{URL}/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_token_signed_with_other_secret_is_rejected(client: TestClient) -> None:
    forged = JwtTokenService("another-secret-key-with-32-bytes-min!!", "HS256", 5)
    res = client.get(
        f"{URL}/me", headers={"Authorization": f"Bearer {forged.create_access_token('1')}"}
    )
    assert res.status_code == 401


def test_login_is_rate_limited(client: TestClient, owner: tuple[int, AuthHeaders]) -> None:
    limiter.enabled = True
    limiter.reset()
    try:
        ok = client.post(f"{URL}/login", data={"username": "owner@test.com", "password": PASSWORD})
        assert ok.status_code == 200
        assert "X-RateLimit-Remaining" in ok.headers
        codes = [
            client.post(
                f"{URL}/login", data={"username": "x@test.com", "password": "bad"}
            ).status_code
            for _ in range(6)
        ]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert codes[:4] == [401] * 4
    assert codes[-1] == 429
