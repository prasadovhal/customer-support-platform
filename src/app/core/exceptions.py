from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)


class AppException(Exception):
    """Base application exception. All custom exceptions derive from this."""

    status_code: int = HTTP_500_INTERNAL_SERVER_ERROR
    error: str = "internal_server_error"
    default_message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.message = message or self.default_message
        self.detail = detail
        self.headers = headers
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = HTTP_404_NOT_FOUND
    error = "not_found"
    default_message = "The requested resource was not found."


class AuthenticationError(AppException):
    status_code = HTTP_401_UNAUTHORIZED
    error = "authentication_error"
    default_message = "Authentication credentials are missing or invalid."

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(message, detail, headers)
        # Always include WWW-Authenticate for 401 responses.
        if self.headers is None:
            self.headers = {}
        self.headers.setdefault("WWW-Authenticate", "Bearer")


class AuthorizationError(AppException):
    status_code = HTTP_403_FORBIDDEN
    error = "authorization_error"
    default_message = "You do not have permission to perform this action."


class ValidationError(AppException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    error = "validation_error"
    default_message = "Request validation failed."


class ConflictError(AppException):
    """Raised when an idempotency conflict is detected or a resource already exists."""

    status_code = HTTP_409_CONFLICT
    error = "conflict"
    default_message = "A conflicting resource or operation already exists."


class ServiceUnavailableError(AppException):
    status_code = HTTP_503_SERVICE_UNAVAILABLE
    error = "service_unavailable"
    default_message = "The service is temporarily unavailable. Please try again later."


def _build_error_response(exc: AppException) -> JSONResponse:
    content: dict[str, Any] = {
        "error": exc.error,
        "message": exc.message,
    }
    if exc.detail is not None:
        content["detail"] = exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach custom exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        return _build_error_response(exc)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return _build_error_response(exc)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return _build_error_response(exc)

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return _build_error_response(exc)

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return _build_error_response(exc)

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(
        request: Request, exc: ConflictError
    ) -> JSONResponse:
        return _build_error_response(exc)

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(
        request: Request, exc: ServiceUnavailableError
    ) -> JSONResponse:
        return _build_error_response(exc)

    # Catch-all for any unhandled Python exceptions so we never leak stack traces.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
            },
        )
