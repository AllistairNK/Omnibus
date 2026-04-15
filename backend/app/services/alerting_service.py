"""
Alerting service for monitoring critical issues and sending notifications.
"""
import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from enum import Enum

from loguru import logger
from app.core.config import settings
from app.core.monitoring import capture_message, monitoring_state


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_RESPONSE = "slow_response"
    HIGH_CPU_USAGE = "high_cpu_usage"
    HIGH_MEMORY_USAGE = "high_memory_usage"
    DATABASE_CONNECTION_ISSUE = "database_connection_issue"
    EXTERNAL_SERVICE_DOWN = "external_service_down"
    SECURITY_ISSUE = "security_issue"
    CUSTOM = "custom"


class Alert:
    """Represents an alert."""
    
    def __init__(self, 
                 alert_type: AlertType,
                 severity: AlertSeverity,
                 title: str,
                 message: str,
                 metadata: Optional[Dict[str, Any]] = None):
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.acknowledged = False
        self.resolved = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() + "Z",
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
        }


class AlertingService:
    """
    Service for managing alerts and notifications.
    """
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        self.alert_cooldown = {
            AlertType.HIGH_ERROR_RATE: timedelta(minutes=5),
            AlertType.SLOW_RESPONSE: timedelta(minutes=10),
            AlertType.HIGH_CPU_USAGE: timedelta(minutes=15),
        }
        self.last_alert_time: Dict[AlertType, datetime] = {}
        
        # Alert thresholds
        self.thresholds = {
            'error_rate': 0.05,  # 5% error rate
            'slow_response_time': 2.0,  # 2 seconds
            'consecutive_errors': 10,
        }
    
    async def check_system_health(self) -> List[Alert]:
        """
        Check system health and generate alerts if needed.
        
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        # Check error rate
        error_rate_alert = await self._check_error_rate()
        if error_rate_alert:
            new_alerts.append(error_rate_alert)
        
        # Check for slow responses (would need performance data)
        # slow_response_alert = await self._check_slow_responses()
        # if slow_response_alert:
        #     new_alerts.append(slow_response_alert)
        
        # Check monitoring state
        monitoring_alerts = await self._check_monitoring_state()
        new_alerts.extend(monitoring_alerts)
        
        # Send alerts
        for alert in new_alerts:
            await self.send_alert(alert)
        
        return new_alerts
    
    async def _check_error_rate(self) -> Optional[Alert]:
        """Check if error rate exceeds threshold."""
        try:
            # Get error rate from monitoring state
            # In a real implementation, this would come from metrics
            error_count = monitoring_state.error_count
            request_count = monitoring_state.request_count
            
            if request_count > 100:  # Only check after sufficient requests
                error_rate = error_count / max(request_count, 1)
                
                if error_rate > self.thresholds['error_rate']:
                    # Check cooldown
                    last_alert = self.last_alert_time.get(AlertType.HIGH_ERROR_RATE)
                    if last_alert and datetime.utcnow() - last_alert < self.alert_cooldown[AlertType.HIGH_ERROR_RATE]:
                        return None
                    
                    alert = Alert(
                        alert_type=AlertType.HIGH_ERROR_RATE,
                        severity=AlertSeverity.ERROR,
                        title="High Error Rate Detected",
                        message=f"Error rate is {error_rate:.1%} ({error_count} errors out of {request_count} requests)",
                        metadata={
                            "error_rate": error_rate,
                            "error_count": error_count,
                            "request_count": request_count,
                            "threshold": self.thresholds['error_rate'],
                        }
                    )
                    
                    self.last_alert_time[AlertType.HIGH_ERROR_RATE] = datetime.utcnow()
                    return alert
                    
        except Exception as e:
            logger.error(f"Error checking error rate: {e}")
        
        return None
    
    async def _check_monitoring_state(self) -> List[Alert]:
        """Check monitoring system state."""
        alerts = []
        
        # Check if Sentry is configured but not working
        # (This would require checking Sentry connectivity)
        
        # Check if monitoring state shows issues
        # For now, just a placeholder for future checks
        
        return alerts
    
    async def send_alert(self, alert: Alert) -> None:
        """
        Send an alert through configured channels.
        
        Args:
            alert: The alert to send
        """
        try:
            # Add to active alerts
            self.alerts.append(alert)
            
            # Keep only recent alerts (last 100)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            # Add to history
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history:]
            
            # Log the alert
            logger.warning(
                f"Alert triggered: {alert.severity.value.upper()} - {alert.title}: {alert.message}"
            )
            
            # Send to Sentry for critical errors
            if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
                capture_message(
                    f"Alert: {alert.title} - {alert.message}",
                    level=alert.severity.value,
                    context=alert.metadata
                )
            
            # Send email notification for critical alerts
            if alert.severity == AlertSeverity.CRITICAL:
                await self._send_email_alert(alert)
            
            # In a production system, you would also:
            # - Send to Slack/Teams
            # - Send to PagerDuty/OpsGenie
            # - Send SMS notifications
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _send_email_alert(self, alert: Alert) -> None:
        """
        Send email notification for critical alerts.
        
        Args:
            alert: The alert to send
        """
        # This is a simplified email implementation
        # In production, use a proper email service or SMTP with authentication
        
        # Check if email alerting is configured
        if not hasattr(settings, 'ALERT_EMAIL_RECIPIENTS') or not settings.ALERT_EMAIL_RECIPIENTS:
            return
        
        try:
            # Simplified email sending
            # In reality, you would configure SMTP settings
            recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', '').split(',')
            
            if not recipients:
                return
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{settings.PROJECT_NAME}] {alert.severity.value.upper()}: {alert.title}"
            msg['From'] = getattr(settings, 'ALERT_EMAIL_FROM', 'alerts@example.com')
            msg['To'] = ', '.join(recipients)
            
            # Create HTML content
            html = f"""
            <html>
            <body>
                <h2>{alert.title}</h2>
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Time:</strong> {alert.timestamp.isoformat()}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Project:</strong> {settings.PROJECT_NAME}</p>
                <p><strong>Environment:</strong> {settings.ENVIRONMENT}</p>
                <hr>
                <p>This is an automated alert from the {settings.PROJECT_NAME} monitoring system.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email (simplified - would need SMTP configuration)
            # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            #     server.starttls()
            #     server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            #     server.send_message(msg)
            
            logger.info(f"Would send email alert to {recipients} for alert: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def acknowledge_alert(self, alert_id: int) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Index of alert in active alerts list
            
        Returns:
            True if acknowledged, False if not found
        """
        try:
            if 0 <= alert_id < len(self.alerts):
                self.alerts[alert_id].acknowledged = True
                logger.info(f"Acknowledged alert: {self.alerts[alert_id].title}")
                return True
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
        
        return False
    
    async def resolve_alert(self, alert_id: int) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Index of alert in active alerts list
            
        Returns:
            True if resolved, False if not found
        """
        try:
            if 0 <= alert_id < len(self.alerts):
                self.alerts[alert_id].resolved = True
                logger.info(f"Resolved alert: {self.alerts[alert_id].title}")
                return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
        
        return False
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all active alerts.
        
        Returns:
            List of alert dictionaries
        """
        return [alert.to_dict() for alert in self.alerts if not alert.resolved]
    
    async def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of historical alerts to return
            
        Returns:
            List of alert dictionaries
        """
        history = self.alert_history[-limit:] if self.alert_history else []
        return [alert.to_dict() for alert in history]
    
    async def create_custom_alert(self,
                                 severity: AlertSeverity,
                                 title: str,
                                 message: str,
                                 metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """
        Create a custom alert.
        
        Args:
            severity: Alert severity
            title: Alert title
            message: Alert message
            metadata: Additional metadata
            
        Returns:
            The created alert
        """
        alert = Alert(
            alert_type=AlertType.CUSTOM,
            severity=severity,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        
        await self.send_alert(alert)
        return alert
    
    async def clear_resolved_alerts(self, older_than_days: int = 7) -> int:
        """
        Clear resolved alerts older than specified days.
        
        Args:
            older_than_days: Clear alerts resolved more than this many days ago
            
        Returns:
            Number of alerts cleared
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)
            
            # Clear from active alerts
            initial_count = len(self.alerts)
            self.alerts = [
                alert for alert in self.alerts
                if not (alert.resolved and alert.timestamp < cutoff_time)
            ]
            
            # Clear from history
            initial_history_count = len(self.alert_history)
            self.alert_history = [
                alert for alert in self.alert_history
                if not (alert.resolved and alert.timestamp < cutoff_time)
            ]
            
            cleared_count = (initial_count - len(self.alerts)) + (initial_history_count - len(self.alert_history))
            logger.info(f"Cleared {cleared_count} resolved alerts older than {older_than_days} days")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Failed to clear resolved alerts: {e}")
            return 0


# Global alerting service instance
alerting_service = AlertingService()


async def start_alert_monitoring() -> None:
    """
    Start background task for monitoring and alerting.
    """
    async def monitor_loop():
        """Background monitoring loop."""
        logger.info("Starting alert monitoring loop")
        
        while True:
            try:
                # Check system health every 60 seconds
                await asyncio.sleep(60)
                
                # Run health checks
                alerts = await alerting_service.check_system_health()
                
                if alerts:
                    logger.info(f"Generated {len(alerts)} alerts from health check")
                    
            except asyncio.CancelledError:
                logger.info("Alert monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    # Start monitoring task
    asyncio.create_task(monitor_loop())
    logger.info("Alert monitoring started")