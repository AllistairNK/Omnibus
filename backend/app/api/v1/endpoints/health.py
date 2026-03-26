"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from loguru import logger

from app.core.database import db
from app.core.middleware import performance_metrics

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Health status information
    """
    logger.debug("Health check requested")
    
    # Check database health if configured
    db_healthy = await db.health_check() if db._pool else True
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "AI Chatbot Backend",
        "version": "0.1.0",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": "2026-03-25T02:08:00Z"  # TODO: Use actual timestamp
    }


@router.get("/health/detailed")
async def detailed_health_check() -> dict:
    """
    Detailed health check with component status.
    
    Returns:
        dict: Detailed health status
    """
    components = {
        "api": {"status": "healthy", "message": "API is responding"},
        "database": {"status": "unknown", "message": "Not configured"},
    }
    
    # Check database if configured
    if db._pool:
        db_healthy = await db.health_check()
        components["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection established" if db_healthy else "Database connection failed"
        }
    
    overall_status = "healthy"
    for component in components.values():
        if component["status"] == "unhealthy":
            overall_status = "degraded"
            break
    
    return {
        "status": overall_status,
        "components": components,
        "uptime": "0d 0h 0m 0s",  # TODO: Implement actual uptime tracking
        "environment": "development"  # TODO: Get from settings
    }


@router.get("/performance")
async def performance_metrics_endpoint() -> dict:
    """
    Performance metrics endpoint.
    
    Returns:
        dict: Performance metrics including response times, request counts, and error rates
    """
    logger.debug("Performance metrics requested")
    
    metrics = performance_metrics.get_metrics()
    
    return {
        "status": "ok",
        "metrics": metrics,
        "timestamp": "2026-03-25T02:08:00Z"  # TODO: Use actual timestamp
    }


@router.post("/performance/reset")
async def reset_performance_metrics() -> dict:
    """
    Reset performance metrics.
    
    Returns:
        dict: Confirmation message
    """
    logger.info("Performance metrics reset requested")
    performance_metrics.reset()
    
    return {
        "status": "ok",
        "message": "Performance metrics reset successfully"
    }