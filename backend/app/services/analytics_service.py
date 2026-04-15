"""
Analytics service for tracking usage metrics and generating insights.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from loguru import logger
from app.core.config import settings
from app.core.monitoring import monitoring_state, capture_message


class AnalyticsService:
    """
    Service for tracking and analyzing usage metrics.
    """
    
    def __init__(self):
        self.usage_data = {
            'daily_requests': defaultdict(int),
            'user_activity': defaultdict(lambda: defaultdict(int)),
            'model_usage': defaultdict(lambda: defaultdict(int)),
            'document_processing': defaultdict(int),
            'error_types': defaultdict(int),
        }
        self.retention_days = 30  # Keep data for 30 days
        
    async def track_request(self, user_id: Optional[str], endpoint: str, 
                           duration: float, status_code: int) -> None:
        """
        Track a request for analytics.
        
        Args:
            user_id: User ID if authenticated
            endpoint: API endpoint
            duration: Request duration in seconds
            status_code: HTTP status code
        """
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Track daily requests
            self.usage_data['daily_requests'][today] += 1
            
            # Track user activity
            if user_id:
                self.usage_data['user_activity'][user_id][today] += 1
            
            # Track endpoint usage
            endpoint_key = endpoint.split('?')[0]  # Remove query params
            self.usage_data['endpoint_usage'] = self.usage_data.get('endpoint_usage', {})
            self.usage_data['endpoint_usage'][endpoint_key] = \
                self.usage_data['endpoint_usage'].get(endpoint_key, 0) + 1
            
            # Track error types
            if status_code >= 400:
                error_type = f"http_{status_code}"
                self.usage_data['error_types'][error_type] += 1
                
                # Capture to Sentry for monitoring
                if status_code >= 500:
                    capture_message(
                        f"Server error {status_code} on {endpoint}",
                        level="error",
                        context={
                            "user_id": user_id,
                            "endpoint": endpoint,
                            "duration": duration,
                        }
                    )
            
            # Clean up old data periodically
            if self.usage_data['daily_requests'].get('_last_cleanup', 0) == 0:
                self.usage_data['daily_requests']['_last_cleanup'] = datetime.utcnow().timestamp()
            
            # Clean up if more than 1 day since last cleanup
            last_cleanup = self.usage_data['daily_requests'].get('_last_cleanup', 0)
            if datetime.utcnow().timestamp() - last_cleanup > 86400:  # 24 hours
                await self._cleanup_old_data()
                self.usage_data['daily_requests']['_last_cleanup'] = datetime.utcnow().timestamp()
                
        except Exception as e:
            logger.error(f"Error tracking request analytics: {e}")
    
    async def track_model_usage(self, user_id: Optional[str], provider: str, 
                               model: str, tokens_used: int, cost: float = 0.0) -> None:
        """
        Track LLM model usage.
        
        Args:
            user_id: User ID if authenticated
            provider: LLM provider (openai, anthropic, gemini)
            model: Model name
            tokens_used: Number of tokens used
            cost: Estimated cost in USD
        """
        try:
            today = datetime.utcnow().date().isoformat()
            key = f"{provider}:{model}"
            
            # Initialize nested dicts if needed
            if 'model_usage_by_day' not in self.usage_data:
                self.usage_data['model_usage_by_day'] = defaultdict(lambda: defaultdict(int))
            if 'model_tokens_by_day' not in self.usage_data:
                self.usage_data['model_tokens_by_day'] = defaultdict(lambda: defaultdict(int))
            if 'model_costs_by_day' not in self.usage_data:
                self.usage_data['model_costs_by_day'] = defaultdict(lambda: defaultdict(float))
            
            # Track usage
            self.usage_data['model_usage_by_day'][today][key] += 1
            self.usage_data['model_tokens_by_day'][today][key] += tokens_used
            self.usage_data['model_costs_by_day'][today][key] += cost
            
            # Track user-specific model usage
            if user_id:
                user_key = f"{user_id}:{key}"
                self.usage_data['user_model_usage'] = self.usage_data.get('user_model_usage', {})
                self.usage_data['user_model_usage'][user_key] = \
                    self.usage_data['user_model_usage'].get(user_key, 0) + 1
            
            # Update monitoring state
            monitoring_state.increment_llm_requests()
            
        except Exception as e:
            logger.error(f"Error tracking model usage: {e}")
    
    async def track_document_processing(self, user_id: Optional[str], 
                                       document_type: str, size_bytes: int) -> None:
        """
        Track document processing activity.
        
        Args:
            user_id: User ID if authenticated
            document_type: Type of document (pdf, txt, docx, md)
            size_bytes: Size of document in bytes
        """
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Initialize if needed
            if 'document_processing_by_day' not in self.usage_data:
                self.usage_data['document_processing_by_day'] = defaultdict(lambda: defaultdict(int))
            if 'document_size_by_day' not in self.usage_data:
                self.usage_data['document_size_by_day'] = defaultdict(lambda: defaultdict(int))
            
            # Track processing
            self.usage_data['document_processing_by_day'][today][document_type] += 1
            self.usage_data['document_size_by_day'][today][document_type] += size_bytes
            
            # Update monitoring state
            monitoring_state.increment_document_processing()
            
        except Exception as e:
            logger.error(f"Error tracking document processing: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Clean up data older than retention period."""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=self.retention_days)).date()
            cutoff_str = cutoff_date.isoformat()
            
            # Clean daily requests
            for date in list(self.usage_data['daily_requests'].keys()):
                if date != '_last_cleanup' and date < cutoff_str:
                    del self.usage_data['daily_requests'][date]
            
            # Clean model usage by day
            if 'model_usage_by_day' in self.usage_data:
                for date in list(self.usage_data['model_usage_by_day'].keys()):
                    if date < cutoff_str:
                        del self.usage_data['model_usage_by_day'][date]
            
            # Clean document processing by day
            if 'document_processing_by_day' in self.usage_data:
                for date in list(self.usage_data['document_processing_by_day'].keys()):
                    if date < cutoff_str:
                        del self.usage_data['document_processing_by_day'][date]
            
            logger.info(f"Cleaned up analytics data older than {cutoff_str}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old analytics data: {e}")
    
    async def get_daily_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get daily metrics for the specified number of days.
        
        Args:
            days: Number of days to include
            
        Returns:
            Dict with daily metrics
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days - 1)
            
            daily_metrics = {}
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.isoformat()
                
                # Get requests for this day
                requests = self.usage_data['daily_requests'].get(date_str, 0)
                
                # Get model usage for this day
                model_usage = {}
                if 'model_usage_by_day' in self.usage_data:
                    model_usage = dict(self.usage_data['model_usage_by_day'].get(date_str, {}))
                
                # Get document processing for this day
                doc_processing = {}
                if 'document_processing_by_day' in self.usage_data:
                    doc_processing = dict(self.usage_data['document_processing_by_day'].get(date_str, {}))
                
                daily_metrics[date_str] = {
                    'requests': requests,
                    'model_usage': model_usage,
                    'document_processing': doc_processing,
                }
                
                current_date += timedelta(days=1)
            
            return daily_metrics
            
        except Exception as e:
            logger.error(f"Error getting daily metrics: {e}")
            return {}
    
    async def get_user_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get activity metrics for a specific user.
        
        Args:
            user_id: User ID
            days: Number of days to include
            
        Returns:
            Dict with user activity metrics
        """
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days - 1)
            
            user_activity = {
                'total_requests': 0,
                'daily_activity': {},
                'model_usage': {},
            }
            
            # Get daily activity
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                activity = self.usage_data['user_activity'].get(user_id, {}).get(date_str, 0)
                if activity > 0:
                    user_activity['daily_activity'][date_str] = activity
                    user_activity['total_requests'] += activity
                current_date += timedelta(days=1)
            
            # Get model usage for this user
            user_prefix = f"{user_id}:"
            if 'user_model_usage' in self.usage_data:
                for key, count in self.usage_data['user_model_usage'].items():
                    if key.startswith(user_prefix):
                        model = key[len(user_prefix):]
                        user_activity['model_usage'][model] = \
                            user_activity['model_usage'].get(model, 0) + count
            
            return user_activity
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return {}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get overall system metrics.
        
        Returns:
            Dict with system metrics
        """
        try:
            # Calculate totals
            total_requests = sum(self.usage_data['daily_requests'].values())
            if '_last_cleanup' in self.usage_data['daily_requests']:
                total_requests -= self.usage_data['daily_requests']['_last_cleanup']
            
            # Get top endpoints
            endpoint_usage = self.usage_data.get('endpoint_usage', {})
            top_endpoints = sorted(
                endpoint_usage.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            # Get model usage summary
            model_summary = {}
            if 'model_usage_by_day' in self.usage_data:
                for day_data in self.usage_data['model_usage_by_day'].values():
                    for model, count in day_data.items():
                        model_summary[model] = model_summary.get(model, 0) + count
            
            # Get error summary
            error_summary = dict(self.usage_data['error_types'])
            
            return {
                'total_requests': total_requests,
                'active_users': len(self.usage_data['user_activity']),
                'top_endpoints': top_endpoints,
                'model_usage_summary': model_summary,
                'error_summary': error_summary,
                'data_retention_days': self.retention_days,
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def export_data(self, format: str = 'json') -> str:
        """
        Export analytics data in specified format.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            if format == 'json':
                # Convert defaultdict to regular dict for JSON serialization
                export_data = {}
                for key, value in self.usage_data.items():
                    if isinstance(value, defaultdict):
                        if key in ['user_activity', 'model_usage', 'document_processing']:
                            # Convert nested defaultdict
                            export_data[key] = {
                                k: dict(v) if isinstance(v, defaultdict) else v
                                for k, v in value.items()
                            }
                        else:
                            export_data[key] = dict(value)
                    else:
                        export_data[key] = value
                
                return json.dumps(export_data, indent=2, default=str)
            
            elif format == 'csv':
                # Simple CSV export of daily requests
                csv_lines = ['date,requests']
                for date, count in sorted(self.usage_data['daily_requests'].items()):
                    if date != '_last_cleanup':
                        csv_lines.append(f'{date},{count}')
                return '\n'.join(csv_lines)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return ""


# Global analytics service instance
analytics_service = AnalyticsService()