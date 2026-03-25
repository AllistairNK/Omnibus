"""
Tests for database migration scripts.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from migrations.run_migrations import (
    get_migration_files,
    ensure_migrations_table,
    get_applied_migrations,
    run_migration,
)


def test_get_migration_files():
    """Test that migration files are discovered in order."""
    with patch("migrations.run_migrations.Path") as mock_path:
        mock_dir = MagicMock()
        mock_path.return_value.parent = mock_dir
        
        # Mock glob to return test files
        mock_file1 = MagicMock()
        mock_file1.name = "001_initial.sql"
        mock_file2 = MagicMock()
        mock_file2.name = "002_data.sql"
        mock_file3 = MagicMock()
        mock_file3.name = "run_migrations.py"  # Should be excluded
        
        mock_dir.glob.return_value = [mock_file3, mock_file1, mock_file2]
        
        files = asyncio.run(get_migration_files())
        
        # Should be sorted and exclude run_migrations.py
        assert len(files) == 2
        assert files[0].name == "001_initial.sql"
        assert files[1].name == "002_data.sql"


@pytest.mark.asyncio
async def test_ensure_migrations_table():
    """Test creation of migrations tracking table."""
    mock_conn = AsyncMock()
    
    await ensure_migrations_table(mock_conn)
    
    mock_conn.execute.assert_called_once()
    call_args = mock_conn.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS _migrations" in call_args


@pytest.mark.asyncio
async def test_get_applied_migrations():
    """Test retrieving applied migrations."""
    mock_conn = AsyncMock()
    
    # Mock successful query
    mock_row1 = {"filename": "001_initial.sql"}
    mock_row2 = {"filename": "002_data.sql"}
    mock_conn.fetch.return_value = [mock_row1, mock_row2]
    
    migrations = await get_applied_migrations(mock_conn)
    
    assert migrations == ["001_initial.sql", "002_data.sql"]
    mock_conn.fetch.assert_called_once_with(
        "SELECT filename FROM _migrations ORDER BY filename"
    )


@pytest.mark.asyncio
async def test_get_applied_migrations_table_not_exists():
    """Test handling when migrations table doesn't exist."""
    mock_conn = AsyncMock()
    mock_conn.fetch.side_effect = Exception("Table doesn't exist")
    
    migrations = await get_applied_migrations(mock_conn)
    
    assert migrations == []
    mock_conn.fetch.assert_called_once()


@pytest.mark.asyncio
async def test_run_migration():
    """Test running a single migration file."""
    mock_conn = AsyncMock()
    mock_file = MagicMock(spec=Path)
    mock_file.name = "001_test.sql"
    mock_file.read_text.return_value = "CREATE TABLE test (id SERIAL);"
    
    await run_migration(mock_conn, mock_file)
    
    # Should execute SQL and record migration
    assert mock_conn.execute.call_count == 2
    
    # First call should be the migration SQL
    first_call = mock_conn.execute.call_args_list[0][0][0]
    assert "CREATE TABLE test" in first_call
    
    # Second call should record the migration
    second_call = mock_conn.execute.call_args_list[1][0][0]
    assert "INSERT INTO _migrations" in second_call


@pytest.mark.asyncio
async def test_run_migration_failure():
    """Test migration failure handling."""
    mock_conn = AsyncMock()
    mock_file = MagicMock(spec=Path)
    mock_file.name = "001_failing.sql"
    mock_file.read_text.return_value = "INVALID SQL;"
    
    # Make execute raise an exception
    mock_conn.execute.side_effect = Exception("SQL syntax error")
    
    with pytest.raises(Exception, match="SQL syntax error"):
        await run_migration(mock_conn, mock_file)


def test_migration_file_content():
    """Test that migration files have valid SQL syntax."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    # Check each SQL migration file
    for sql_file in migrations_dir.glob("*.sql"):
        if sql_file.name == "run_migrations.py":
            continue
            
        content = sql_file.read_text(encoding="utf-8")
        
        # Basic validation
        assert len(content) > 0, f"Migration file {sql_file.name} is empty"
        
        # Check for common SQL statements
        sql_lower = content.lower()
        if "001_initial" in sql_file.name:
            assert "create table" in sql_lower, f"Initial schema should create tables"
        elif "002_sample" in sql_file.name:
            assert "insert into" in sql_lower, f"Sample data should have INSERT statements"
        
        # Check file naming convention
        assert sql_file.name.startswith("0"), f"Migration files should start with zero-padded number: {sql_file.name}"
        assert "_" in sql_file.name, f"Migration files should use underscores: {sql_file.name}"
        assert sql_file.name.endswith(".sql"), f"Migration files should have .sql extension: {sql_file.name}"