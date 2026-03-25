"""
Tests for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(test_client: TestClient) -> None:
    """Test health check endpoint returns expected response."""
    response = test_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "api_version" in data
    assert data["environment"] == "testing"


def test_health_endpoint_structure(test_client: TestClient) -> None:
    """Test health endpoint response structure."""
    response = test_client.get("/health")
    data = response.json()
    
    expected_keys = {"status", "service", "version", "environment", "api_version"}
    assert set(data.keys()) == expected_keys


def test_health_endpoint_with_invalid_method(test_client: TestClient) -> None:
    """Test health endpoint with invalid HTTP method."""
    response = test_client.post("/health")
    assert response.status_code == 405  # Method Not Allowed


@pytest.mark.asyncio
async def test_health_endpoint_async(async_client) -> None:
    """Test health endpoint using async client."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"