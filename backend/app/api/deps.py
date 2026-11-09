"""Composition root for each request: wires adapters into use cases."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.use_cases.auth import AuthService
from app.application.use_cases.tasks import TaskService
from app.core.config import Settings, get_settings
from app.domain.entities import User
from app.infrastructure.celery_app import CeleryNotificationDispatcher
from app.infrastructure.persistence.database import session_scope
from app.infrastructure.persistence.repositories import (
    SqlAlchemyTaskRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.security import BcryptPasswordHasher, JwtTokenService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_session(request: Request) -> Iterator[Session]:
    yield from session_scope(request.app.state.session_factory)


def get_notifier(request: Request) -> object:
    return getattr(request.app.state, "notifier", None) or CeleryNotificationDispatcher()


SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    return AuthService(
        users=SqlAlchemyUserRepository(session),
        hasher=BcryptPasswordHasher(),
        tokens=JwtTokenService(
            settings.jwt_secret_key, settings.jwt_algorithm, settings.access_token_expire_minutes
        ),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], auth: AuthServiceDep) -> User:
    return auth.resolve_user(token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_task_service(
    session: SessionDep, notifier: Annotated[object, Depends(get_notifier)]
) -> TaskService:
    return TaskService(
        tasks=SqlAlchemyTaskRepository(session),
        users=SqlAlchemyUserRepository(session),
        notifier=notifier,  # type: ignore[arg-type]
    )


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
