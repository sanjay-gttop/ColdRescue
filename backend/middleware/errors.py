"""ColdRescue global error handler middleware."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.schemas.errors import ErrorDetail, ErrorResponse


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(l) for l in first_error.get("loc", []))
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=first_error.get("msg", "Validation failed"),
                field=field or None,
            )
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
            )
        ).model_dump(),
    )
