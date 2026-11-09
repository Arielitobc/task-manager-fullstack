from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import PasswordHasher, TokenService, UserRepository
from app.domain.entities import User
from app.domain.exceptions import AuthenticationError, ConflictError, ValidationError

MIN_PASSWORD_LENGTH = 8


@dataclass
class AuthService:
    users: UserRepository
    hasher: PasswordHasher
    tokens: TokenService

    def register(self, email: str, full_name: str, password: str) -> User:
        email = email.strip().lower()
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )
        if self.users.get_by_email(email):
            raise ConflictError("A user with this email already exists")
        user = User(
            email=email,
            full_name=full_name.strip(),
            hashed_password=self.hasher.hash(password),
        )
        return self.users.add(user)

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email.strip().lower())
        # Same error for unknown email and wrong password: avoids user enumeration.
        if not user or not self.hasher.verify(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        return self.tokens.create_access_token(str(user.id))

    def resolve_user(self, token: str) -> User:
        try:
            user_id = int(self.tokens.decode_subject(token))
        except (ValueError, AuthenticationError) as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        user = self.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid or expired token")
        return user
