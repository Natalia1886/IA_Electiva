"""Centralized exception handlers registered on the FastAPI application.

Every unhandled exception that reaches the API boundaries is normalized here
into a JSON response with a stable shape:
    * application errors  -> ``{"detail", "code"?, "details"?}`` with their status
    * request validation   -> 422 with the original error list (frontend-compatible)
    * HTTP exceptions      -> ``{"detail": ...}`` preserving headers (WWW-Authenticate)
    * DB integrity errors  -> 409 (duplicated key / FK violation)
    * any other error      -> 500 ``{"detail": "Error interno del servidor"}``
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import MilanError

logger = logging.getLogger("milan")


async def milan_error_handler(request: Request, exc: MilanError) -> JSONResponse:
    body: dict[str, Any] = {"detail": exc.message}
    if exc.code:
        body["code"] = exc.code
    if exc.details is not None:
        body["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=body)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    headers: dict[str, str] = getattr(exc, "headers", None) or {}
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    logger.warning("Petición inválida [%s]: %s", request.url.path, errors)
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Violación de integridad en [%s]: %s", request.url.path, exc.orig)
    return JSONResponse(
        status_code=409,
        content={"detail": "La operación entra en conflicto con los datos existentes (clave duplicada o referencia inválida)."},
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every centralized handler to the application."""
    app.add_exception_handler(MilanError, milan_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)