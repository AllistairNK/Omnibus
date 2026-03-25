"""
Pytest configuration and fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.config import settings
from app.core.database import db


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment() -> AsyncGenerator:
    """Set up test environment before all tests."""
    # Override settings for testing
    settings.DEBUG = True
    settings.ENVIRONMENT = "testing"
    settings.DATABASE_URL = None  # Use test database in real tests

    # Initialize database (if needed)
    await db.connect()
    
    yield
    
    # Cleanup
    await db.disconnect()


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for FastAPI."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI."""
    from httpx import AsyncClient
    from httpx._transports.asgi import ASGITransport
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def test_settings() -> settings:
    """Get test settings."""
    return settings