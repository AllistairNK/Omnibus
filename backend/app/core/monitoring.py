"""
Monitoring and observability configuration for the application.
Includes Sentry integration, performance monitoring, and metrics collection.
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration
from loguru import logger

from app.core.config import settings


def configure_sentry() -> None:
    """
    Configure Sentry for error tracking and performance monitoring.
    Only initializes if SENTRY_DSN is provided.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not provided, skipping Sentry configuration")
        return
    
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
                SqlalchemyIntegration(),
                HttpxIntegration(),
                LoguruIntegration(),
            ],
            # Set debug to True only in development
            debug=settings.DEBUG,
            # Associate users with errors
            send_default_pii=True,
            # Customize event grouping
            before_send=lambda event, hint: before_send_filter(event, hint),
            # Release information
            release=f"{settings.PROJECT_NAME}@{settings.VERSION}",
        )
        logger.info(f"Sentry configured for environment: {settings.SENTRY_ENVIRONMENT}")
    except Exception as e:
        logger.error(f"Failed to configure Sentry: {e}")


def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry.
    Can be used to filter out specific errors or add custom context.
    """
    # Filter out specific error types if needed
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        # Example: Filter out specific exceptions
        if exc_type.__name__ == "ConnectionError":
            return None
    
    # Add custom tags
    event.setdefault("tags", {}).update({
        "project": settings.PROJECT_NAME,
        "environment": settings.SENTRY_ENVIRONMENT,
    })
    
    # Add user context if available
    # This would typically come from request context
    # event.setdefault("user", {}).update(user_context)
    
    return event


def capture_exception(error: Exception, context: dict = None) -> None:
    """
    Capture an exception with additional context.
    
    Args:
        error: The exception to capture
        context: Additional context dictionary
    """
    if settings.SENTRY_DSN:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(error)
    else:
        # Log locally if Sentry is not configured
        logger.error(f"Uncaptured exception: {error}", exc_info=True)


def capture_message(message: str, level: str = "info", context: dict = None) -> None:
    """
    Capture a message with a specific level.
    
    Args:
        message: The message to capture
        level: Message level (info, warning, error, fatal)
        context: Additional context dictionary
    """
    if settings.SENTRY_DSN:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level)
    else:
        # Log locally if Sentry is not configured
        log_func = getattr(logger, level, logger.info)
        log_func(f"Uncaptured message: {message}")


def start_transaction(name: str, op: str = "http.server") -> sentry_sdk.tracing.Span:
    """
    Start a performance monitoring transaction.
    
    Args:
        name: Transaction name
        op: Operation type
        
    Returns:
        The transaction span
    """
    if settings.SENTRY_DSN and settings.ENABLE_PERFORMANCE_MONITORING:
        transaction = sentry_sdk.start_transaction(name=name, op=op)
        return transaction
    return None


def set_user_context(user_id: str = None, email: str = None, username: str = None) -> None:
    """
    Set user context for Sentry events.
    
    Args:
        user_id: User ID
        email: User email
        username: Username
    """
    if settings.SENTRY_DSN:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username,
        })


def clear_user_context() -> None:
    """Clear user context from Sentry."""
    if settings.SENTRY_DSN:
        sentry_sdk.set_user(None)


# Global monitoring state
class MonitoringState:
    """Global monitoring state for the application."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        self.llm_requests = 0
        self.document_processing_count = 0
    
    def increment_request_count(self):
        self.request_count += 1
    
    def increment_error_count(self):
        self.error_count += 1
    
    def increment_llm_requests(self):
        self.llm_requests += 1
    
    def increment_document_processing(self):
        self.document_processing_count += 1
    
    def get_metrics(self) -> dict:
        """Get current monitoring metrics."""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "active_connections": self.active_connections,
            "llm_requests": self.llm_requests,
            "document_processing_count": self.document_processing_count,
        }


# Global monitoring state instance
monitoring_state = MonitoringState()