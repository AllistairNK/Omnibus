#!/usr/bin/env python3
"""
Mark a migration as already applied in the migrations table.
Useful when a migration needs to be skipped (e.g., requires admin privileges).
"""
import asyncio
import logging
import os

import asyncpg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def mark_migration_applied(migration_filename: str):
    """Mark a migration as already applied."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        logger.info("Please set DATABASE_URL in your .env file")
        return

    logger.info(f"Marking migration as applied: {migration_filename}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Ensure migrations table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64)
            )
        """)
        
        # Mark migration as applied
        await conn.execute("""
            INSERT INTO _migrations (filename, applied_at)
            VALUES ($1, NOW())
            ON CONFLICT (filename) DO NOTHING
        """, migration_filename)
        
        logger.info(f"Migration {migration_filename} marked as applied")
        
        await conn.close()
        logger.info("Done")
        
    except Exception as e:
        logger.error(f"Failed to mark migration as applied: {e}")
        raise

if __name__ == "__main__":
    # Mark migration 004_storage_rls_policies.sql as applied
    asyncio.run(mark_migration_applied("004_storage_rls_policies.sql"))