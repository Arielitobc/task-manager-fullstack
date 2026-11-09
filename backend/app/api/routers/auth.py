from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep, CurrentUser
from app.api.schemas import ErrorResponse, Token, UserCreate, UserRead
from app.core.config import get_settings
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
@limiter.limit(get_settings().rate_limit_login)
def register(
    request: Request, response: Response, body: UserCreate, auth: AuthServiceDep
) -> UserRead:
    # `request`/`response` are required by slowapi to evaluate limits and inject headers.
    user = auth.register(body.email, body.full_name, body.password)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token, responses={401: {"model": ErrorResponse}})
@limiter.limit(get_settings().rate_limit_login)
def login(
    request: Request,
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth: AuthServiceDep,
) -> Token:
    """OAuth2 password flow: send `username` (the email) and `password` as form data."""
    return Token(access_token=auth.login(form.username, form.password))


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
