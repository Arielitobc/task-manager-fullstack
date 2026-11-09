import pytest

from app.application.use_cases.auth import AuthService
from app.domain.exceptions import AuthenticationError, ConflictError, ValidationError
from tests.fakes import FakeHasher, FakeTokenService, InMemoryUserRepository


@pytest.fixture
def service() -> AuthService:
    return AuthService(InMemoryUserRepository(), FakeHasher(), FakeTokenService())


def test_register_normalizes_email_and_hashes_password(service: AuthService) -> None:
    user = service.register(" Ana@Example.com ", "Ana", "secret123")
    assert user.email == "ana@example.com"
    assert user.hashed_password != "secret123"


def test_register_rejects_short_password(service: AuthService) -> None:
    with pytest.raises(ValidationError):
        service.register("a@b.com", "A", "short")


def test_register_rejects_duplicate_email(service: AuthService) -> None:
    service.register("a@b.com", "A", "secret123")
    with pytest.raises(ConflictError):
        service.register("A@B.com", "A", "secret123")


def test_login_returns_token(service: AuthService) -> None:
    user = service.register("a@b.com", "A", "secret123")
    token = service.login("a@b.com", "secret123")
    assert service.resolve_user(token).id == user.id


@pytest.mark.parametrize(("email", "password"), [("a@b.com", "wrong-pass"), ("x@y.com", "x")])
def test_login_with_bad_credentials_fails(service: AuthService, email: str, password: str) -> None:
    service.register("a@b.com", "A", "secret123")
    with pytest.raises(AuthenticationError):
        service.login(email, password)


def test_inactive_user_cannot_login(service: AuthService) -> None:
    user = service.register("a@b.com", "A", "secret123")
    user.is_active = False
    with pytest.raises(AuthenticationError):
        service.login("a@b.com", "secret123")


@pytest.mark.parametrize("token", ["garbage", "token::abc", "token::999"])
def test_resolve_user_rejects_invalid_tokens(service: AuthService, token: str) -> None:
    with pytest.raises(AuthenticationError):
        service.resolve_user(token)
