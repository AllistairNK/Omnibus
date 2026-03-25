#!/usr/bin/env python3
"""
Database migration runner for Supabase PostgreSQL.
Run migrations in order to set up the database schema.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import List

import asyncpg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

MIGRATIONS_DIR = Path(__file__).parent


async def get_migration_files() -> List[Path]:
    """Get migration files in order."""
    migration_files = sorted(
        [f for f in MIGRATIONS_DIR.glob("*.sql") if f.name != "run_migrations.py"],
        key=lambda x: x.name,
    )
    logger.info(f"Found {len(migration_files)} migration files")
    return migration_files


async def run_migration(conn: asyncpg.Connection, migration_file: Path) -> None:
    """Run a single migration file."""
    logger.info(f"Running migration: {migration_file.name}")
    
    try:
        # Read SQL file
        sql_content = migration_file.read_text(encoding="utf-8")
        
        # Execute migration
        await conn.execute(sql_content)
        
        # Record migration in migrations table
        await conn.execute("""
            INSERT INTO _migrations (filename, applied_at)
            VALUES ($1, NOW())
            ON CONFLICT (filename) DO NOTHING
        """, migration_file.name)
        
        logger.info(f"Migration {migration_file.name} completed successfully")
        
    except Exception as e:
        logger.error(f"Migration {migration_file.name} failed: {e}")
        raise


async def ensure_migrations_table(conn: asyncpg.Connection) -> None:
    """Create migrations tracking table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            checksum VARCHAR(64)
        )
    """)
    logger.info("Migrations table ensured")


async def get_applied_migrations(conn: asyncpg.Connection) -> List[str]:
    """Get list of already applied migrations."""
    try:
        rows = await conn.fetch("SELECT filename FROM _migrations ORDER BY filename")
        return [row["filename"] for row in rows]
    except Exception:
        # Table might not exist yet
        return []


async def main() -> None:
    """Run all pending migrations."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        logger.info("Please set DATABASE_URL in your .env file")
        return

    logger.info(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Ensure migrations table exists
        await ensure_migrations_table(conn)
        
        # Get applied migrations
        applied = await get_applied_migrations(conn)
        logger.info(f"Already applied migrations: {len(applied)}")
        
        # Get all migration files
        migration_files = await get_migration_files()
        
        # Run pending migrations
        for migration_file in migration_files:
            if migration_file.name in applied:
                logger.info(f"Skipping already applied: {migration_file.name}")
                continue
                
            await run_migration(conn, migration_file)
        
        # Final status
        final_applied = await get_applied_migrations(conn)
        logger.info(f"Total applied migrations: {len(final_applied)}")
        
        await conn.close()
        logger.info("Migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())