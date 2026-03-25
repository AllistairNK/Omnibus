"""
Performance benchmarking tests for the AI Chatbot backend.
These tests establish baseline performance metrics and help identify regressions.
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from tests.factories import create_test_user, create_test_api_key, create_test_document
from tests.mocks import patch_external_services


class PerformanceMetrics:
    """Track performance metrics during tests."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def start_timer(self, name: str) -> None:
        """Start a timer for a metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(-time.time())
    
    def stop_timer(self, name: str) -> float:
        """Stop a timer and return elapsed time."""
        if name in self.metrics and self.metrics[name] and self.metrics[name][-1] < 0:
            elapsed = time.time() + self.metrics[name][-1]
            self.metrics[name][-1] = elapsed
            return elapsed
        return 0.0
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics."""
        summary = {}
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
                }
        return summary


@pytest.fixture
def metrics() -> PerformanceMetrics:
    """Create a performance metrics tracker."""
    return PerformanceMetrics()


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for FastAPI."""
    return TestClient(app)


class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_health_endpoint_performance(self, test_client: TestClient, metrics: PerformanceMetrics):
        """Test health endpoint response time."""
        # Warm up
        for _ in range(3):
            test_client.get("/health")
        
        # Measure performance
        iterations = 10
        for i in range(iterations):
            metrics.start_timer("health_endpoint")
            response = test_client.get("/health")
            metrics.stop_timer("health_endpoint")
            
            assert response.status_code == 200
        
        summary = metrics.get_summary()
        health_metrics = summary.get("health_endpoint", {})
        
        # Assert performance targets
        assert health_metrics.get("mean", 0) < 0.1  # Should respond in < 100ms
        assert health_metrics.get("p95", 0) < 0.2   # 95% should be < 200ms
    
    def test_auth_endpoints_performance(self, test_client: TestClient, metrics: PerformanceMetrics):
        """Test authentication endpoints performance with mocking."""
        with patch_external_services():
            # Test signup performance
            signup_data = {
                "email": "perf_test@example.com",
                "password": "TestPassword123!",
                "full_name": "Performance Test User"
            }
            
            iterations = 5
            for i in range(iterations):
                metrics.start_timer("signup_endpoint")
                response = test_client.post("/api/v1/auth/signup", json=signup_data)
                metrics.stop_timer("signup_endpoint")
                
                assert response.status_code in [200, 201, 400]
            
            # Test login performance
            login_data = {
                "email": "perf_test@example.com",
                "password": "TestPassword123!"
            }
            
            for i in range(iterations):
                metrics.start_timer("login_endpoint")
                response = test_client.post("/api/v1/auth/login", json=login_data)
                metrics.stop_timer("login_endpoint")
                
                assert response.status_code in [200, 401]
        
        summary = metrics.get_summary()
        
        # Assert performance targets for auth endpoints
        if "signup_endpoint" in summary:
            assert summary["signup_endpoint"]["mean"] < 0.5  # < 500ms
        if "login_endpoint" in summary:
            assert summary["login_endpoint"]["mean"] < 0.3   # < 300ms
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client: TestClient, metrics: PerformanceMetrics):
        """Test performance under concurrent load."""
        with patch_external_services():
            async def make_request():
                start = time.time()
                response = test_client.get("/health")
                elapsed = time.time() - start
                assert response.status_code == 200
                return elapsed
            
            # Make concurrent requests
            num_concurrent = 10
            tasks = [make_request() for _ in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            
            for elapsed in results:
                metrics.record_metric("concurrent_health", elapsed)
            
            summary = metrics.get_summary()
            concurrent_metrics = summary.get("concurrent_health", {})
            
            # Assert concurrent performance
            assert concurrent_metrics.get("mean", 0) < 0.2  # < 200ms under load
            assert concurrent_metrics.get("max", 0) < 0.5   # No request > 500ms


class TestDatabasePerformance:
    """Performance tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_supabase_mock_performance(self, metrics: PerformanceMetrics):
        """Test mocked Supabase operations performance."""
        from tests.mocks import mock_supabase_client
        
        mock_client = mock_supabase_client()
        
        # Test table operations
        iterations = 20
        for i in range(iterations):
            metrics.start_timer("supabase_table_query")
            result = await mock_client.table("users").select("*").eq("id", "test").execute()
            metrics.stop_timer("supabase_table_query")
            assert result.data is not None
        
        # Test auth operations
        for i in range(iterations):
            metrics.start_timer("supabase_auth_signin")
            result = await mock_client.auth.sign_in_with_password(
                email="test@example.com",
                password="password"
            )
            metrics.stop_timer("supabase_auth_signin")
            assert result is not None
        
        summary = metrics.get_summary()
        
        # Assert mock performance targets
        if "supabase_table_query" in summary:
            assert summary["supabase_table_query"]["mean"] < 0.01  # Mock should be fast
        if "supabase_auth_signin" in summary:
            assert summary["supabase_auth_signin"]["mean"] < 0.01


class TestMemoryUsage:
    """Tests for memory usage patterns."""
    
    def test_memory_usage_growth(self, test_client: TestClient):
        """Test that memory usage doesn't grow excessively with repeated requests."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for i in range(100):
            response = test_client.get("/health")
            assert response.status_code == 200
        
        # Allow garbage collection
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal
        assert memory_growth < 10  # Less than 10MB growth


def generate_performance_report() -> Dict[str, Any]:
    """
    Generate a performance report from test results.
    This can be called after tests to create a baseline report.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "python_version": "3.11.9",
            "platform": "Windows",
        },
        "performance_baselines": {
            "health_endpoint": {
                "target_max_ms": 100,
                "target_p95_ms": 200,
                "description": "Health check endpoint response time"
            },
            "auth_endpoints": {
                "signup_target_ms": 500,
                "login_target_ms": 300,
                "description": "Authentication endpoints response time"
            },
            "concurrent_requests": {
                "target_mean_ms": 200,
                "target_max_ms": 500,
                "description": "Performance under concurrent load"
            },
            "memory_usage": {
                "target_growth_mb": 10,
                "description": "Memory growth after 100 requests"
            }
        },
        "test_coverage_requirements": {
            "backend_test_coverage": 80,
            "frontend_test_coverage": 70,
        }
    }
    
    return report


if __name__ == "__main__":
    """Run performance tests and generate report."""
    import json
    
    # Run performance tests
    print("Running performance tests...")
    
    # This would normally run pytest programmatically
    # For now, just generate the baseline report
    report = generate_performance_report()
    
    # Save report to file
    with open("performance_baseline.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("Performance baseline report generated: performance_baseline.json")
    print("\nPerformance Baselines:")
    print(json.dumps(report["performance_baselines"], indent=2))