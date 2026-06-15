#!/usr/bin/env python3
"""
Run a single migration file manually.
Useful when a migration fails and needs to be run separately.
"""
import asyncio
import logging
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def run_single_migration(migration_filename: str):
    """Run a single migration file."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        logger.info("Please set DATABASE_URL in your .env file")
        return

    migration_file = Path(__file__).parent / migration_filename
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_filename}")
        return

    logger.info(f"Running single migration: {migration_filename}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Read SQL file
        sql_content = migration_file.read_text(encoding="utf-8")
        
        # Execute migration
        await conn.execute(sql_content)
        
        # Record migration in migrations table
        await conn.execute("""
            INSERT INTO _migrations (filename, applied_at)
            VALUES ($1, NOW())
            ON CONFLICT (filename) DO NOTHING
        """, migration_filename)
        
        logger.info(f"Migration {migration_filename} completed successfully")
        
        await conn.close()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration {migration_filename} failed: {e}")
        raise

if __name__ == "__main__":
    # Run migration 005_add_user_role_column.sql
    asyncio.run(run_single_migration("005_add_user_role_column.sql"))