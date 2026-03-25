"""
Integration tests for Supabase database operations.
These tests require a Supabase instance or test database.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.supabase import SupabaseClient


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    with patch("app.core.supabase.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        # Mock auth methods
        mock_client.auth = MagicMock()
        mock_client.auth.sign_up = AsyncMock()
        mock_client.auth.sign_in_with_password = AsyncMock()
        mock_client.auth.sign_out = AsyncMock()
        mock_client.auth.get_user = AsyncMock()
        
        # Mock storage methods
        mock_client.storage = MagicMock()
        mock_storage_from = MagicMock()
        mock_client.storage.from_ = MagicMock(return_value=mock_storage_from)
        mock_storage_from.upload = AsyncMock()
        mock_storage_from.get_public_url = AsyncMock()
        mock_storage_from.remove = AsyncMock()
        
        # Mock table methods
        mock_client.table = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert = MagicMock(return_value=mock_table)
        mock_table.select = MagicMock(return_value=mock_table)
        mock_table.update = MagicMock(return_value=mock_table)
        mock_table.delete = MagicMock(return_value=mock_table)
        mock_table.eq = MagicMock(return_value=mock_table)
        
        mock_response = MagicMock()
        mock_response.data = [{"id": "test-id"}]
        mock_table.execute = AsyncMock(return_value=mock_response)
        
        yield mock_client


@pytest.mark.asyncio
async def test_supabase_client_initialization(mock_supabase_client):
    """Test Supabase client initialization."""
    # Reset singleton
    SupabaseClient._instance = None
    SupabaseClient._client = None
    
    client = SupabaseClient()
    assert client is not None
    assert client._client is not None


@pytest.mark.asyncio
async def test_sign_up(mock_supabase_client):
    """Test user sign up."""
    client = SupabaseClient()
    
    # Mock response
    mock_response = {"user": {"id": "test-id", "email": "test@example.com"}}
    mock_supabase_client.auth.sign_up.return_value = mock_response
    
    result = await client.sign_up("test@example.com", "password123")
    
    assert result == mock_response
    mock_supabase_client.auth.sign_up.assert_called_once_with({
        "email": "test@example.com",
        "password": "password123",
    })


@pytest.mark.asyncio
async def test_sign_in(mock_supabase_client):
    """Test user sign in."""
    client = SupabaseClient()
    
    mock_response = {
        "user": {"id": "test-id", "email": "test@example.com"},
        "session": {"access_token": "test-token"}
    }
    mock_supabase_client.auth.sign_in_with_password.return_value = mock_response
    
    result = await client.sign_in("test@example.com", "password123")
    
    assert result == mock_response
    mock_supabase_client.auth.sign_in_with_password.assert_called_once_with({
        "email": "test@example.com",
        "password": "password123",
    })


@pytest.mark.asyncio
async def test_upload_file(mock_supabase_client):
    """Test file upload to Supabase Storage."""
    client = SupabaseClient()
    
    mock_response = {"id": "file-id", "path": "uploads/test.txt"}
    mock_storage_from = mock_supabase_client.storage.from_.return_value
    mock_storage_from.upload.return_value = mock_response
    
    file_content = b"Test file content"
    result = await client.upload_file("documents", "test.txt", file_content)
    
    assert result == mock_response
    mock_supabase_client.storage.from_.assert_called_once_with("documents")
    mock_storage_from.upload.assert_called_once_with(
        path="test.txt",
        file=file_content,
        file_options={"content-type": "text/plain"},
    )


@pytest.mark.asyncio
async def test_insert_record(mock_supabase_client):
    """Test inserting a record into a table."""
    client = SupabaseClient()
    
    mock_response = {"id": "record-id", "name": "Test Record"}
    mock_table = mock_supabase_client.table.return_value
    mock_table.insert.return_value.execute.return_value.data = [mock_response]
    
    data = {"name": "Test Record", "value": 123}
    result = await client.insert("test_table", data)
    
    assert result == mock_response
    mock_supabase_client.table.assert_called_once_with("test_table")
    mock_table.insert.assert_called_once_with(data)


@pytest.mark.asyncio
async def test_select_records(mock_supabase_client):
    """Test selecting records from a table."""
    client = SupabaseClient()
    
    mock_data = [
        {"id": "1", "name": "Test 1"},
        {"id": "2", "name": "Test 2"},
    ]
    mock_table = mock_supabase_client.table.return_value
    mock_table.select.return_value.eq.return_value.execute.return_value.data = mock_data
    
    filters = {"status": "active"}
    result = await client.select("test_table", "*", filters)
    
    assert result == mock_data
    mock_supabase_client.table.assert_called_once_with("test_table")
    mock_table.select.assert_called_once_with("*")
    mock_table.eq.assert_called_once_with("status", "active")


@pytest.mark.asyncio
async def test_update_record(mock_supabase_client):
    """Test updating records in a table."""
    client = SupabaseClient()
    
    mock_data = [{"id": "1", "name": "Updated Name"}]
    mock_table = mock_supabase_client.table.return_value
    mock_table.update.return_value.eq.return_value.execute.return_value.data = mock_data
    
    update_data = {"name": "Updated Name"}
    filters = {"id": "1"}
    result = await client.update("test_table", update_data, filters)
    
    assert result == mock_data
    mock_supabase_client.table.assert_called_once_with("test_table")
    mock_table.update.assert_called_once_with(update_data)
    mock_table.eq.assert_called_once_with("id", "1")


@pytest.mark.asyncio
async def test_delete_record(mock_supabase_client):
    """Test deleting records from a table."""
    client = SupabaseClient()
    
    mock_data = [{"id": "1", "deleted": True}]
    mock_table = mock_supabase_client.table.return_value
    mock_table.delete.return_value.eq.return_value.execute.return_value.data = mock_data
    
    filters = {"id": "1"}
    result = await client.delete("test_table", filters)
    
    assert result == mock_data
    mock_supabase_client.table.assert_called_once_with("test_table")
    mock_table.delete.assert_called_once()
    mock_table.eq.assert_called_once_with("id", "1")


@pytest.mark.asyncio
async def test_get_current_user(mock_supabase_client):
    """Test getting current authenticated user."""
    client = SupabaseClient()
    
    mock_user = {"id": "user-id", "email": "test@example.com"}
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase_client.auth.get_user.return_value = mock_response
    
    result = await client.get_current_user()
    
    assert result == mock_user
    mock_supabase_client.auth.get_user.assert_called_once()


@pytest.mark.asyncio
async def test_sign_out(mock_supabase_client):
    """Test user sign out."""
    client = SupabaseClient()
    
    await client.sign_out()
    
    mock_supabase_client.auth.sign_out.assert_called_once()


def test_singleton_pattern():
    """Test that SupabaseClient follows singleton pattern."""
    # Reset singleton
    SupabaseClient._instance = None
    SupabaseClient._client = None
    
    # Mock the initialization to avoid actual Supabase connection
    with patch.object(SupabaseClient, '_initialize'):
        client1 = SupabaseClient()
        client2 = SupabaseClient()
        
        assert client1 is client2
        assert id(client1) == id(client2)