"""
Custom middleware for request logging and error handling.
"""
import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()

        # Log request
        logger.debug(
            f"Request: {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            # Log unhandled exceptions
            logger.error(
                f"Unhandled exception: {exc}",
                exc_info=True,
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc) if request.app.debug else "Internal server error",
                },
            )

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={process_time:.3f}s"
        )

        # Add X-Process-Time header
        response.headers["X-Process-Time"] = str(process_time)

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and formatting errors."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error handling."""
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                f"Error processing request {request.method} {request.url.path}: {exc}",
                exc_info=True,
            )

            # Return standardized error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "detail": str(exc) if request.app.debug else None,
                },
            )