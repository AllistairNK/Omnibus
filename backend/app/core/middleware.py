"""
Custom middleware for request logging and error handling.
"""
import time
import traceback
from typing import Callable, Optional, Dict, List
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.services.analytics_service import analytics_service


class PerformanceMetrics:
    """Performance metrics collector for response time monitoring."""
    
    def __init__(self):
        self.metrics = {
            'endpoint_times': defaultdict(list),
            'total_requests': 0,
            'error_count': 0,
            'start_time': datetime.now()
        }
        self.slow_threshold = 1.0  # 1 second
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """Record a request's performance metrics."""
        self.metrics['total_requests'] += 1
        self.metrics['endpoint_times'][endpoint].append(duration)
        
        # Keep only last 1000 measurements per endpoint
        if len(self.metrics['endpoint_times'][endpoint]) > 1000:
            self.metrics['endpoint_times'][endpoint] = self.metrics['endpoint_times'][endpoint][-1000:]
        
        if status_code >= 400:
            self.metrics['error_count'] += 1
        
        # Log slow requests
        if duration > self.slow_threshold:
            logger.warning(f"Slow request detected: {endpoint} took {duration:.3f}s")
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics."""
        endpoint_stats = {}
        for endpoint, times in self.metrics['endpoint_times'].items():
            if times:
                endpoint_stats[endpoint] = {
                    'count': len(times),
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'p95': sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
                    'slow_count': sum(1 for t in times if t > self.slow_threshold)
                }
        
        uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'total_requests': self.metrics['total_requests'],
            'error_count': self.metrics['error_count'],
            'error_rate': self.metrics['error_count'] / max(self.metrics['total_requests'], 1),
            'endpoint_stats': endpoint_stats,
            'slow_threshold': self.slow_threshold
        }
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = {
            'endpoint_times': defaultdict(list),
            'total_requests': 0,
            'error_count': 0,
            'start_time': datetime.now()
        }


# Global performance metrics instance
performance_metrics = PerformanceMetrics()


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
            # Log unhandled exceptions with full traceback
            import traceback
            traceback.print_exc()
            logger.opt(exception=True).error(f"Unhandled exception: {exc}")
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

        # Record performance metrics
        endpoint = f"{request.method} {request.url.path}"
        performance_metrics.record_request(endpoint, process_time, response.status_code)

        # Track analytics (async fire-and-forget)
        try:
            # Extract user ID from request if available
            user_id = None
            if hasattr(request.state, 'user') and request.state.user:
                user_id = request.state.user.get('id')
            elif 'Authorization' in request.headers:
                # Try to extract from auth header
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    # In a real implementation, you would decode the JWT
                    # For now, we'll just track as authenticated user
                    user_id = 'authenticated'
            
            # Track request in analytics service
            import asyncio
            asyncio.create_task(
                analytics_service.track_request(
                    user_id=user_id,
                    endpoint=request.url.path,
                    duration=process_time,
                    status_code=response.status_code
                )
            )
        except Exception as e:
            logger.warning(f"Failed to track analytics: {e}")

        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Performance-Metrics"] = "enabled"

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