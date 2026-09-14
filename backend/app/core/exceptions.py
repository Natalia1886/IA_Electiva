"""Centralized application-level exceptions.

All domain errors raised anywhere in the backend derive from :class:`MilanError`
so a single registered handler can translate them into a uniform JSON body
``{"detail": ..., "code"?: ..., "details"?: ...}``.

Handlers also cover the framework-level errors (validation, HTTP, integrity)
and any unexpected exception, so the API always returns structured JSON.
"""
from typing import Any


class MilanError(Exception):
    """Base class for every application error."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str | None = None,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class BadRequestError(MilanError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=400, **kwargs)


class UnauthorizedError(MilanError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=401, **kwargs)


class ForbiddenError(MilanError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(MilanError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=404, **kwargs)


class ConflictError(MilanError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=409, **kwargs)


class ServiceUnavailableError(MilanError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, status_code=503, **kwargs)