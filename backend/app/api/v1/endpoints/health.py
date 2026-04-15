"""
Health check and monitoring endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.core.config import settings
from app.core.database import db
from app.core.middleware import performance_metrics
from app.core.monitoring import monitoring_state
from app.services.alerting_service import alerting_service, start_alert_monitoring

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
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z"
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
    
    # Calculate uptime from performance metrics
    metrics = performance_metrics.get_metrics()
    uptime_seconds = metrics.get('uptime_seconds', 0)
    
    # Format uptime
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    return {
        "status": overall_status,
        "components": components,
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/performance")
async def performance_metrics_endpoint() -> dict:
    """
    Performance metrics endpoint.
    
    Returns:
        dict: Performance metrics including response times, request counts, and error rates
    """
    logger.debug("Performance metrics requested")
    
    # Get performance metrics from middleware
    perf_metrics = performance_metrics.get_metrics()
    
    # Get application monitoring metrics
    app_metrics = monitoring_state.get_metrics()
    
    # Combine metrics
    combined_metrics = {
        "performance": perf_metrics,
        "application": app_metrics,
        "monitoring": {
            "sentry_enabled": bool(settings.SENTRY_DSN),
            "performance_monitoring_enabled": settings.ENABLE_PERFORMANCE_MONITORING,
            "metrics_endpoint_enabled": settings.METRICS_ENDPOINT_ENABLED,
        }
    }
    
    return {
        "status": "ok",
        "metrics": combined_metrics,
        "timestamp": datetime.utcnow().isoformat() + "Z"
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


@router.get("/metrics")
async def prometheus_metrics() -> str:
    """
    Prometheus-style metrics endpoint (OpenMetrics format).
    
    Returns:
        str: Metrics in Prometheus exposition format
    """
    logger.debug("Prometheus metrics requested")
    
    # Get all metrics
    perf_metrics = performance_metrics.get_metrics()
    app_metrics = monitoring_state.get_metrics()
    
    # Build Prometheus metrics
    lines = []
    
    # Application info
    lines.append(f'ai_chatbot_info{{project="{settings.PROJECT_NAME}",version="{settings.VERSION}",environment="{settings.ENVIRONMENT}"}} 1')
    
    # Performance metrics
    lines.append(f'ai_chatbot_uptime_seconds {perf_metrics.get("uptime_seconds", 0)}')
    lines.append(f'ai_chatbot_total_requests {perf_metrics.get("total_requests", 0)}')
    lines.append(f'ai_chatbot_error_count {perf_metrics.get("error_count", 0)}')
    lines.append(f'ai_chatbot_error_rate {perf_metrics.get("error_rate", 0)}')
    
    # Application metrics
    lines.append(f'ai_chatbot_llm_requests_total {app_metrics.get("llm_requests", 0)}')
    lines.append(f'ai_chatbot_document_processing_total {app_metrics.get("document_processing_count", 0)}')
    lines.append(f'ai_chatbot_active_connections {app_metrics.get("active_connections", 0)}')
    
    # Endpoint-specific metrics
    for endpoint, stats in perf_metrics.get("endpoint_stats", {}).items():
        # Sanitize endpoint name for Prometheus label
        endpoint_label = endpoint.replace("/", "_").replace("-", "_").replace(".", "_")
        lines.append(f'ai_chatbot_endpoint_request_count{{endpoint="{endpoint}"}} {stats.get("count", 0)}')
        lines.append(f'ai_chatbot_endpoint_response_time_seconds{{endpoint="{endpoint}",quantile="avg"}} {stats.get("avg", 0)}')
        lines.append(f'ai_chatbot_endpoint_response_time_seconds{{endpoint="{endpoint}",quantile="min"}} {stats.get("min", 0)}')
        lines.append(f'ai_chatbot_endpoint_response_time_seconds{{endpoint="{endpoint}",quantile="max"}} {stats.get("max", 0)}')
        lines.append(f'ai_chatbot_endpoint_response_time_seconds{{endpoint="{endpoint}",quantile="0.95"}} {stats.get("p95", 0)}')
        lines.append(f'ai_chatbot_endpoint_slow_request_count{{endpoint="{endpoint}"}} {stats.get("slow_count", 0)}')
    
    # Add timestamp
    lines.append(f"# HELP ai_chatbot_metrics_timestamp Unix timestamp when metrics were collected")
    lines.append(f"# TYPE ai_chatbot_metrics_timestamp gauge")
    lines.append(f"ai_chatbot_metrics_timestamp {int(datetime.utcnow().timestamp())}")
    
    return "\n".join(lines)


@router.get("/alerts")
async def get_alerts(active_only: bool = True) -> dict:
    """
    Get active alerts.
    
    Args:
        active_only: If True, only return non-resolved alerts
        
    Returns:
        dict: List of alerts
    """
    if active_only:
        alerts = await alerting_service.get_active_alerts()
    else:
        alerts = await alerting_service.get_alert_history(limit=100)
    
    return {
        "status": "ok",
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int) -> dict:
    """
    Acknowledge an alert.
    
    Args:
        alert_id: ID of alert to acknowledge
        
    Returns:
        dict: Acknowledgement status
    """
    success = await alerting_service.acknowledge_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "status": "ok",
        "message": f"Alert {alert_id} acknowledged",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int) -> dict:
    """
    Resolve an alert.
    
    Args:
        alert_id: ID of alert to resolve
        
    Returns:
        dict: Resolution status
    """
    success = await alerting_service.resolve_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "status": "ok",
        "message": f"Alert {alert_id} resolved",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/alerts/check")
async def trigger_health_check() -> dict:
    """
    Trigger a manual health check and return any new alerts.
    
    Returns:
        dict: Health check results and new alerts
    """
    alerts = await alerting_service.check_system_health()
    
    return {
        "status": "ok",
        "message": f"Health check completed, found {len(alerts)} new alerts",
        "alerts": [alert.to_dict() for alert in alerts],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.on_event("startup")
async def startup_event():
    """Start alert monitoring on application startup."""
    await start_alert_monitoring()