"""
Logging configuration for the application.
"""
import logging
import sys
from typing import Any

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Safely get message, handling potential UnicodeDecodeError
        try:
            message = record.getMessage()
        except UnicodeDecodeError:
            # If message contains binary data, convert to safe representation
            if isinstance(record.msg, bytes):
                message = f"<binary data length={len(record.msg)}>"
            else:
                message = str(record.msg)
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, message
        )


def configure_logging() -> None:
    """Configure logging for the application."""
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Add file handler in production
    if not settings.DEBUG:
        logger.add(
            "logs/app.log",
            rotation="500 MB",
            retention="10 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    # Set root logger level to WARNING to suppress DEBUG/INFO logs from third-party libraries
    logging.getLogger().setLevel(logging.WARNING)

    # Set loguru as handler for uvicorn and other loggers
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "httpx", "httpcore", "supabase", "logging"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
        # Set level to WARNING to avoid DEBUG logs that may contain binary data
        logging_logger.setLevel(logging.WARNING)

    logger.info(f"Logging configured for {settings.PROJECT_NAME} ({settings.ENVIRONMENT})")