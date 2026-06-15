"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware, AuthenticationMiddleware
from app.core.monitoring import configure_sentry


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    # Configure logging before app creation
    configure_logging()
    
    # Configure Sentry for error tracking and monitoring
    configure_sentry()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API for AI Chatbot with RAG",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        openapi_tags=[
            {
                "name": "health",
                "description": "Health check endpoints for monitoring",
            },
            {
                "name": "auth",
                "description": "Authentication and authorization endpoints",
            },
            {
                "name": "users",
                "description": "User profile management endpoints",
            },
            {
                "name": "api-keys",
                "description": "API key management for third-party services",
            },
            {
                "name": "documents",
                "description": "Document metadata management endpoints",
            },
        ],
        redirect_slashes=False,
    )

    # Set up CORS - allow all origins in development
    # Note: In production, you should restrict this to specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Root health check endpoint (for monitoring tools)
    @app.get("/health")
    async def root_health_check() -> dict:
        """Root health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "api_version": "v1",
        }

    return app


app = create_application()