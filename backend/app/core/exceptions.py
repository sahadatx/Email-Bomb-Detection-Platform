from typing import Any


class AppException(Exception):
    """
    Base exception for application-level errors.
    """

    status_code: int = 400
    code: str = "application_error"

    def __init__(
        self,
        message: str,
        *,
        details: Any = None,
    ) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class AuthenticationError(AppException):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(AppException):
    status_code = 403
    code = "authorization_error"


class ResourceNotFoundError(AppException):
    status_code = 404
    code = "resource_not_found"


class ConflictError(AppException):
    status_code = 409
    code = "conflict"


class ValidationError(AppException):
    status_code = 422
    code = "validation_error"