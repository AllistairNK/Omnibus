"""
Factory functions for generating test data.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import MagicMock

from app.core.config import settings


def create_test_user(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    is_active: bool = True,
    is_superuser: bool = False,
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a test user dictionary."""
    if user_id is None:
        user_id = str(uuid.uuid4())
    if email is None:
        email = f"test_{user_id[:8]}@example.com"
    if full_name is None:
        full_name = f"Test User {user_id[:8]}"
    if created_at is None:
        created_at = datetime.utcnow()

    return {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "is_active": is_active,
        "is_superuser": is_superuser,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
    }


def create_test_api_key(
    key_id: Optional[str] = None,
    user_id: Optional[str] = None,
    provider: str = "openai",
    encrypted_key: Optional[str] = None,
    is_active: bool = True,
    created_at: Optional[datetime] = None,
    last_used_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a test API key dictionary."""
    if key_id is None:
        key_id = str(uuid.uuid4())
    if user_id is None:
        user_id = str(uuid.uuid4())
    if encrypted_key is None:
        encrypted_key = f"encrypted_{key_id}"
    if created_at is None:
        created_at = datetime.utcnow()

    return {
        "id": key_id,
        "user_id": user_id,
        "provider": provider,
        "encrypted_key": encrypted_key,
        "is_active": is_active,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
        "last_used_at": last_used_at.isoformat() if last_used_at else None,
    }


def create_test_document(
    document_id: Optional[str] = None,
    user_id: Optional[str] = None,
    filename: Optional[str] = None,
    file_size: int = 1024,
    mime_type: str = "application/pdf",
    storage_path: Optional[str] = None,
    status: str = "uploaded",
    metadata: Optional[Dict[str, Any]] = None,
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a test document dictionary."""
    if document_id is None:
        document_id = str(uuid.uuid4())
    if user_id is None:
        user_id = str(uuid.uuid4())
    if filename is None:
        filename = f"test_document_{document_id[:8]}.pdf"
    if storage_path is None:
        storage_path = f"documents/{user_id}/{document_id}/{filename}"
    if created_at is None:
        created_at = datetime.utcnow()
    if metadata is None:
        metadata = {
            "pages": 10,
            "author": "Test Author",
            "title": "Test Document",
        }

    return {
        "id": document_id,
        "user_id": user_id,
        "filename": filename,
        "file_size": file_size,
        "mime_type": mime_type,
        "storage_path": storage_path,
        "status": status,
        "metadata": metadata,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
        "processed_at": None,
    }


def create_test_chat_session(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    title: Optional[str] = None,
    model: str = "gpt-5-nano",
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a test chat session dictionary."""
    if session_id is None:
        session_id = str(uuid.uuid4())
    if user_id is None:
        user_id = str(uuid.uuid4())
    if title is None:
        title = f"Test Chat Session {session_id[:8]}"
    if created_at is None:
        created_at = datetime.utcnow()

    return {
        "id": session_id,
        "user_id": user_id,
        "title": title,
        "model": model,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
    }


def create_test_chat_message(
    message_id: Optional[str] = None,
    session_id: Optional[str] = None,
    role: str = "user",
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a test chat message dictionary."""
    if message_id is None:
        message_id = str(uuid.uuid4())
    if session_id is None:
        session_id = str(uuid.uuid4())
    if content is None:
        content = f"This is a test {role} message."
    if created_at is None:
        created_at = datetime.utcnow()
    if metadata is None:
        metadata = {
            "tokens": 50,
            "model": "gpt-5-nano",
        }

    return {
        "id": message_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "metadata": metadata,
        "created_at": created_at.isoformat(),
    }


def create_mock_supabase_response(
    data: Optional[list] = None,
    count: Optional[int] = None,
    error: Optional[str] = None,
) -> MagicMock:
    """Create a mock Supabase response."""
    mock_response = MagicMock()
    mock_response.data = data or []
    mock_response.count = count or len(mock_response.data)
    if error:
        mock_response.error = MagicMock()
        mock_response.error.message = error
    else:
        mock_response.error = None
    return mock_response


def create_mock_supabase_auth_response(
    user: Optional[Dict[str, Any]] = None,
    session: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> MagicMock:
    """Create a mock Supabase auth response."""
    mock_response = MagicMock()
    
    if user is None:
        user = create_test_user()
    
    mock_response.user = MagicMock()
    mock_response.user.id = user["id"]
    mock_response.user.email = user["email"]
    mock_response.user.user_metadata = {"full_name": user["full_name"]}
    
    if session:
        mock_response.session = MagicMock()
        mock_response.session.access_token = f"access_token_{user['id']}"
        mock_response.session.refresh_token = f"refresh_token_{user['id']}"
        mock_response.session.expires_at = int(
            (datetime.utcnow() + timedelta(hours=1)).timestamp()
        )
    else:
        mock_response.session = None
    
    if error:
        mock_response.error = MagicMock()
        mock_response.error.message = error
    else:
        mock_response.error = None
    
    return mock_response