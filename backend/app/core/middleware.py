"""
Custom middleware for request logging and error handling.
"""
import time
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


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


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication and user attachment."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication."""
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        user = None
        if token:
            try:
                # Decode token using Supabase JWT secret
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
                sub = payload.get("sub")
                email = payload.get("email")
                if sub and email:
                    user = {
                        "id": sub,
                        "email": email,
                        "role": payload.get("role"),
                        "app_metadata": payload.get("app_metadata"),
                        "user_metadata": payload.get("user_metadata"),
                    }
            except JWTError:
                # Invalid token - treat as no authentication
                pass

        # Attach user to request state
        request.state.user = user

        return await call_next(request)