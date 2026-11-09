from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.schemas import UserRead
from app.infrastructure.persistence.repositories import SqlAlchemyUserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(_: CurrentUser, session: SessionDep) -> list[UserRead]:
    """Active users, used to pick an assignee."""
    return [UserRead.model_validate(u) for u in SqlAlchemyUserRepository(session).list_active()]
