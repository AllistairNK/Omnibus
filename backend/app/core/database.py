"""
Database connection pool using asyncpg.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
from loguru import logger

from app.core.config import settings


class Database:
    """Database connection pool manager."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self._pool: Optional[asyncpg.Pool] = None
        self._connection_url: Optional[str] = None

    async def connect(self) -> None:
        """Create connection pool."""
        if not settings.DATABASE_URL:
            logger.warning("DATABASE_URL not set, database connections disabled")
            return

        self._connection_url = str(settings.DATABASE_URL)
        logger.info(f"Connecting to database: {self._connection_url}")

        try:
            self._pool = await asyncpg.create_pool(
                dsn=self._connection_url,
                min_size=1,
                max_size=settings.DATABASE_POOL_SIZE,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
            )
            logger.info(
                f"Database connection pool created (size: {settings.DATABASE_POOL_SIZE})"
            )
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")
            self._pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection from the pool."""
        if not self._pool:
            raise RuntimeError("Database pool not initialized")

        connection = await self._pool.acquire()
        try:
            yield connection
        finally:
            await self._pool.release(connection)

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection and start a transaction."""
        async with self.acquire() as connection:
            async with connection.transaction():
                yield connection

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status."""
        async with self.acquire() as conn:
            result = await conn.execute(query, *args)
            return result

    async def fetch(self, query: str, *args) -> list:
        """Execute a query and fetch all rows."""
        async with self.acquire() as conn:
            result = await conn.fetch(query, *args)
            return result

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Execute a query and fetch one row."""
        async with self.acquire() as conn:
            result = await conn.fetchrow(query, *args)
            return result

    async def fetchval(self, query: str, *args) -> Optional[any]:
        """Execute a query and fetch a single value."""
        async with self.acquire() as conn:
            result = await conn.fetchval(query, *args)
            return result

    async def health_check(self) -> bool:
        """Check database health."""
        if not self._pool:
            return False

        try:
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
db = Database()


async def get_database() -> Database:
    """Get database instance for dependency injection."""
    return db