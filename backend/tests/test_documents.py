"""
Unit and integration tests for document endpoints, including file upload.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app
from app.core.supabase import SupabaseClient
from app.core.auth import get_current_user


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for document tests."""
    with patch("app.core.supabase.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        # Mock auth methods
        mock_client.auth = MagicMock()
        mock_client.auth.get_user = AsyncMock()
        
        # Mock storage methods
        mock_client.storage = MagicMock()
        mock_storage_from = MagicMock()
        mock_client.storage.from_ = MagicMock(return_value=mock_storage_from)
        mock_storage_from.upload = AsyncMock()
        mock_storage_from.remove = AsyncMock()
        mock_storage_from.get_public_url = MagicMock(return_value="https://example.com/file.pdf")
        
        # Mock table methods
        mock_client.table = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select = MagicMock(return_value=mock_table)
        mock_table.eq = MagicMock(return_value=mock_table)
        mock_table.insert = MagicMock(return_value=mock_table)
        mock_table.update = MagicMock(return_value=mock_table)
        mock_table.delete = MagicMock(return_value=mock_table)
        mock_table.range = MagicMock(return_value=mock_table)
        mock_table.order = MagicMock(return_value=mock_table)
        mock_table.execute = MagicMock()
        
        yield mock_client


@pytest.fixture
def test_client():
    """Test client for FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock the get_current_user dependency."""
    with patch("app.core.auth.get_current_user") as mock:
        mock.return_value = {
            "access_token": "test_token",
            "user": {
                "id": "test_user_id",
                "email": "test@example.com"
            }
        }
        yield mock


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return {
        "access_token": "test_token",
        "user": {
            "id": "test_user_id",
            "email": "test@example.com"
        }
    }


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content for testing."""
    # Simple PDF header (not a real PDF, but enough for testing)
    return b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[]/Count 0>>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\ntrailer\n<</Size 3/Root 1 0 R>>\nstartxref\n149\n%%EOF"


class TestDocumentUpload:
    """Test suite for document upload endpoint."""
    
    def test_upload_document_success(self, test_client, mock_supabase_client, mock_current_user, sample_pdf_content):
        """Test successful document upload."""
        # Mock storage upload response
        mock_supabase_client.storage.from_().upload.return_value = {"id": "storage_id"}
        
        # Mock database insert response
        mock_db_response = MagicMock()
        mock_db_response.data = [{
            "id": "doc_123",
            "user_id": "test_user_id",
            "filename": "test.pdf",
            "file_path": "documents/test_user_id/uuid.pdf",
            "file_size": 1024,
            "file_type": "pdf",
            "uploaded_at": "2026-03-25T00:00:00Z",
            "processed_at": None,
            "chunk_count": 0,
            "status": "uploaded",
            "metadata": {}
        }]
        mock_supabase_client.table().insert().execute.return_value = mock_db_response
        
        # Create test file
        files = {
            "file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")
        }
        data = {
            "metadata": json.dumps({"source": "test"})
        }
        
        # Make request (no auth header needed since get_current_user is mocked)
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data
        )
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["id"] == "doc_123"
        assert response_data["filename"] == "test.pdf"
        assert response_data["file_type"] == "pdf"
        assert response_data["status"] == "uploaded"
        
        # Verify storage upload was called
        mock_supabase_client.storage.from_().upload.assert_called_once()
        
        # Verify database insert was called
        mock_supabase_client.table().insert().execute.assert_called_once()
    
    def test_upload_document_file_too_large(self, test_client, mock_supabase_client, mock_auth_user):
        """Test upload with file exceeding size limit."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        # Create large file content (exceeds 100MB default limit)
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        
        files = {
            "file": ("test.pdf", BytesIO(large_content), "application/pdf")
        }
        
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "exceeds maximum limit" in response.json()["detail"]
    
    def test_upload_document_invalid_file_type(self, test_client, mock_supabase_client, mock_auth_user, sample_pdf_content):
        """Test upload with disallowed file type."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        files = {
            "file": ("test.exe", BytesIO(sample_pdf_content), "application/octet-stream")
        }
        
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not allowed" in response.json()["detail"]
    
    def test_upload_document_no_filename(self, test_client, mock_supabase_client, mock_auth_user, sample_pdf_content):
        """Test upload with empty filename."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        files = {
            "file": ("", BytesIO(sample_pdf_content), "application/pdf")
        }
        
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Filename is required" in response.json()["detail"]
    
    def test_upload_document_storage_failure(self, test_client, mock_supabase_client, mock_auth_user, sample_pdf_content):
        """Test upload when storage upload fails."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        # Mock storage upload to raise exception
        mock_supabase_client.storage.from_().upload.side_effect = Exception("Storage error")
        
        files = {
            "file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")
        }
        
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to upload file" in response.json()["detail"]
    
    def test_upload_document_invalid_metadata_json(self, test_client, mock_supabase_client, mock_auth_user, sample_pdf_content):
        """Test upload with invalid metadata JSON."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        # Mock storage upload response
        mock_supabase_client.storage.from_().upload.return_value = {"id": "storage_id"}
        
        # Mock database insert response
        mock_db_response = MagicMock()
        mock_db_response.data = [{
            "id": "doc_123",
            "user_id": "test_user_id",
            "filename": "test.pdf",
            "file_path": "documents/test_user_id/uuid.pdf",
            "file_size": 1024,
            "file_type": "pdf",
            "uploaded_at": "2026-03-25T00:00:00Z",
            "processed_at": None,
            "chunk_count": 0,
            "status": "uploaded",
            "metadata": {"raw_metadata": "invalid json"}
        }]
        mock_supabase_client.table().insert().execute.return_value = mock_db_response
        
        files = {
            "file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")
        }
        data = {
            "metadata": "invalid json"
        }
        
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should still succeed but with raw metadata stored
        assert response.status_code == status.HTTP_201_CREATED
        assert "raw_metadata" in response.json()["metadata"]


class TestDocumentDeleteWithStorage:
    """Test suite for document deletion with storage cleanup."""
    
    def test_delete_document_with_storage(self, test_client, mock_supabase_client, mock_auth_user):
        """Test document deletion including storage file removal."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        # Mock document exists response
        mock_select_response = MagicMock()
        mock_select_response.data = [{
            "id": "doc_123",
            "user_id": "test_user_id",
            "file_path": "documents/test_user_id/uuid.pdf"
        }]
        mock_supabase_client.table().select().eq().eq().execute.return_value = mock_select_response
        
        # Mock delete responses
        mock_supabase_client.storage.from_().remove.return_value = {"success": True}
        mock_delete_response = MagicMock()
        mock_supabase_client.table().delete().eq().eq().execute.return_value = mock_delete_response
        
        response = test_client.delete(
            "/api/v1/documents/doc_123",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify storage deletion was called
        mock_supabase_client.storage.from_().remove.assert_called_once_with(["documents/test_user_id/uuid.pdf"])
        
        # Verify database deletion was called
        mock_supabase_client.table().delete().eq().eq().execute.assert_called_once()
    
    def test_delete_document_storage_failure_continues(self, test_client, mock_supabase_client, mock_auth_user):
        """Test document deletion continues even if storage deletion fails."""
        # Mock auth response
        mock_user_response = MagicMock()
        mock_user_response.user = MagicMock()
        mock_user_response.user.id = "test_user_id"
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        # Mock document exists response
        mock_select_response = MagicMock()
        mock_select_response.data = [{
            "id": "doc_123",
            "user_id": "test_user_id",
            "file_path": "documents/test_user_id/uuid.pdf"
        }]
        mock_supabase_client.table().select().eq().eq().execute.return_value = mock_select_response
        
        # Mock storage deletion to fail
        mock_supabase_client.storage.from_().remove.side_effect = Exception("Storage error")
        
        # Mock database deletion
        mock_delete_response = MagicMock()
        mock_supabase_client.table().delete().eq().eq().execute.return_value = mock_delete_response
        
        response = test_client.delete(
            "/api/v1/documents/doc_123",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should still succeed (204) even if storage deletion fails
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify database deletion was still called
        mock_supabase_client.table().delete().eq().eq().execute.assert_called_once()


class TestDocumentValidation:
    """Test suite for document validation logic."""
    
    def test_allowed_file_types_config(self):
        """Test that configuration includes expected file types."""
        from app.core.config import settings
        assert "pdf" in settings.ALLOWED_FILE_TYPES
        assert "txt" in settings.ALLOWED_FILE_TYPES
        assert "docx" in settings.ALLOWED_FILE_TYPES
        assert "md" in settings.ALLOWED_FILE_TYPES
    
    def test_max_upload_size_config(self):
        """Test that max upload size is configured."""
        from app.core.config import settings
        assert hasattr(settings, "MAX_UPLOAD_SIZE_MB")
        assert isinstance(settings.MAX_UPLOAD_SIZE_MB, int)
        assert settings.MAX_UPLOAD_SIZE_MB > 0