"""Domain-level errors. The API layer maps them to HTTP status codes."""


class DomainError(Exception):
    """Base class for all business errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass
