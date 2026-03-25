"""
Tests for chat session and message management endpoints.
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import get_current_user
from app.services.llm_service import llm_service

client = TestClient(app)


# Mock user for authentication
mock_user = {
    "id": "test-user-id",
    "email": "test@example.com",
    "role": "user",
    "app_metadata": {},
    "user_metadata": {},
}


def override_get_current_user():
    """Override dependency to return mock user."""
    return mock_user


app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock Supabase client for all tests."""
    with patch("app.api.v1.endpoints.chats.SupabaseClient") as mock_supabase_class:
        mock_supabase = MagicMock()
        mock_supabase._client = MagicMock()
        mock_supabase_class.return_value = mock_supabase
        yield mock_supabase


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    with patch("app.api.v1.endpoints.chats.llm_service") as mock_service:
        mock_service._initialized = True
        mock_service.is_available = AsyncMock(return_value=True)
        mock_service.initialize = AsyncMock()
        mock_service.chat_completion = AsyncMock()
        mock_service.chat_completion_stream = AsyncMock()
        yield mock_service


class TestChatEndpoints:
    """Test chat session management endpoints."""
    
    def test_create_chat(self, mock_supabase):
        """Test creating a new chat session."""
        # Mock database response
        mock_supabase._client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "test-chat-id",
            "user_id": mock_user["id"],
            "title": "Test Chat",
            "model_used": "gpt-4",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }]
        
        response = client.post(
            "/api/v1/chats/",
            json={
                "title": "Test Chat",
                "model_used": "gpt-4",
                "metadata": {},
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Chat"
        assert data["user_id"] == mock_user["id"]
        assert data["model_used"] == "gpt-4"
        assert "id" in data
    
    def test_list_chats(self, mock_supabase):
        """Test listing chat sessions."""
        # Mock chats response
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.data = [
            {
                "id": "chat-1",
                "user_id": mock_user["id"],
                "title": "Chat 1",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "model_used": "gpt-4",
                "metadata": {},
            },
            {
                "id": "chat-2",
                "user_id": mock_user["id"],
                "title": "Chat 2",
                "created_at": "2024-01-02T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
                "model_used": "gpt-3.5",
                "metadata": {},
            },
        ]
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.count = 2
        
        # Mock message counts
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 5
        
        response = client.get("/api/v1/chats/?page=1&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["chats"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["chats"][0]["title"] == "Chat 1"
        assert data["chats"][0]["message_count"] == 5
    
    def test_get_chat(self, mock_supabase):
        """Test getting a specific chat session."""
        chat_id = "test-chat-id"
        
        # Mock chat response
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "user_id": mock_user["id"],
            "title": "Test Chat",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "model_used": "gpt-4",
            "metadata": {},
        }]
        
        # Mock message count
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 3
        
        response = client.get(f"/api/v1/chats/{chat_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == chat_id
        assert data["title"] == "Test Chat"
        assert data["message_count"] == 3
    
    def test_get_chat_not_found(self, mock_supabase):
        """Test getting a non-existent chat session."""
        chat_id = "non-existent-id"
        
        # Mock empty response
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.get(f"/api/v1/chats/{chat_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_chat(self, mock_supabase):
        """Test updating a chat session."""
        chat_id = "test-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        # Mock update response
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "user_id": mock_user["id"],
            "title": "Updated Chat Title",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
            "model_used": "gpt-4",
            "metadata": {"key": "value"},
        }]
        
        # Mock message count
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 5
        
        response = client.put(
            f"/api/v1/chats/{chat_id}",
            json={
                "title": "Updated Chat Title",
                "metadata": {"key": "value"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Chat Title"
        assert data["metadata"] == {"key": "value"}
    
    def test_delete_chat(self, mock_supabase):
        """Test deleting a chat session."""
        chat_id = "test-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        response = client.delete(f"/api/v1/chats/{chat_id}")
        
        assert response.status_code == 204
    
    def test_delete_chat_not_found(self, mock_supabase):
        """Test deleting a non-existent chat session."""
        chat_id = "non-existent-id"
        
        # Mock empty response for exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.delete(f"/api/v1/chats/{chat_id}")
        
        assert response.status_code == 404


class TestMessageEndpoints:
    """Test message management endpoints."""
    
    def test_create_message(self, mock_supabase):
        """Test creating a new message in a chat."""
        chat_id = "test-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        # Mock message insert
        mock_supabase._client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "test-message-id",
            "chat_id": chat_id,
            "role": "user",
            "content": "Hello, world!",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {},
            "tokens_used": 10,
            "model": "gpt-4",
        }]
        
        # Mock chat update
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "updated_at": "2024-01-01T00:00:01",
        }]
        
        response = client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={
                "role": "user",
                "content": "Hello, world!",
                "metadata": {},
                "tokens_used": 10,
                "model": "gpt-4",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["chat_id"] == chat_id
        assert data["role"] == "user"
        assert data["content"] == "Hello, world!"
        assert data["tokens_used"] == 10
    
    def test_create_message_invalid_role(self, mock_supabase):
        """Test creating a message with invalid role."""
        chat_id = "test-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        response = client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={
                "role": "invalid-role",
                "content": "Hello, world!",
            },
        )
        
        assert response.status_code == 400
        assert "role" in response.json()["detail"].lower()
    
    def test_list_messages(self, mock_supabase):
        """Test listing messages in a chat."""
        chat_id = "test-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        # Mock messages response
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.data = [
            {
                "id": "msg-1",
                "chat_id": chat_id,
                "role": "user",
                "content": "Hello!",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": {},
            },
            {
                "id": "msg-2",
                "chat_id": chat_id,
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": "2024-01-01T00:00:01",
                "metadata": {},
            },
        ]
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value.count = 2
        
        response = client.get(f"/api/v1/chats/{chat_id}/messages?page=1&page_size=50")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["total"] == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
    
    def test_get_message(self, mock_supabase):
        """Test getting a specific message."""
        chat_id = "test-chat-id"
        message_id = "test-message-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        # Mock message response
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            "id": message_id,
            "chat_id": chat_id,
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {},
        }]
        
        response = client.get(f"/api/v1/chats/{chat_id}/messages/{message_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message_id
        assert data["content"] == "Test message"
    
    def test_delete_message(self, mock_supabase):
        """Test deleting a message."""
        chat_id = "test-chat-id"
        message_id = "test-message-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": chat_id}]
        
        # Mock message exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"id": message_id}]
        
        # Mock chat update
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "updated_at": "2024-01-01T00:00:01",
        }]
        
        response = client.delete(f"/api/v1/chats/{chat_id}/messages/{message_id}")
        
        assert response.status_code == 204


class TestChatCompletionEndpoints:
    """Test chat completion endpoints."""
    
    def test_chat_completion_new_chat(self, mock_supabase, mock_llm_service):
        """Test chat completion with new chat."""
        # Mock LLM response
        mock_llm_service.chat_completion.return_value = {
            "content": "Hello! How can I help you?",
            "role": "assistant",
            "model": "gpt-4",
            "tokens_used": 25,
            "finish_reason": "stop",
        }
        
        # Mock chat insert
        mock_supabase._client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "new-chat-id",
            "user_id": mock_user["id"],
            "title": "Test message...",
            "model_used": "gpt-4",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }]
        
        # Mock message inserts
        mock_supabase._client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "test-message-id",
            "chat_id": "new-chat-id",
            "role": "assistant",
            "content": "Hello! How can I help you?",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {},
            "tokens_used": 25,
            "model": "gpt-4",
        }]
        
        # Mock chat update
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": "new-chat-id",
            "updated_at": "2024-01-01T00:00:01",
        }]
        
        response = client.post(
            "/api/v1/chats/completions",
            json={
                "message": "Test message",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello! How can I help you?"
        assert data["role"] == "assistant"
        assert data["model"] == "gpt-4"
        assert "chat_id" in data
        assert "message_id" in data
    
    def test_chat_completion_existing_chat(self, mock_supabase, mock_llm_service):
        """Test chat completion with existing chat."""
        chat_id = "existing-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "user_id": mock_user["id"],
            "title": "Existing Chat",
            "model_used": "gpt-4",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }]
        
        # Mock previous messages
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "prev-msg-1",
                "chat_id": chat_id,
                "role": "user",
                "content": "Previous message",
                "timestamp": "2024-01-01T00:00:00",
            },
            {
                "id": "prev-msg-2",
                "chat_id": chat_id,
                "role": "assistant",
                "content": "Previous response",
                "timestamp": "2024-01-01T00:00:01",
            },
        ]
        
        # Mock LLM response
        mock_llm_service.chat_completion.return_value = {
            "content": "Response to new message",
            "role": "assistant",
            "model": "gpt-4",
            "tokens_used": 30,
            "finish_reason": "stop",
        }
        
        # Mock message inserts
        mock_supabase._client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "test-message-id",
            "chat_id": chat_id,
            "role": "assistant",
            "content": "Response to new message",
            "timestamp": "2024-01-01T00:00:02",
            "metadata": {},
            "tokens_used": 30,
            "model": "gpt-4",
        }]
        
        # Mock chat update
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "updated_at": "2024-01-01T00:00:02",
        }]
        
        response = client.post(
            "/api/v1/chats/completions",
            json={
                "message": "New message",
                "chat_id": chat_id,
                "model": "gpt-4",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["chat_id"] == chat_id
        assert data["content"] == "Response to new message"
    
    def test_chat_completion_llm_unavailable(self, mock_supabase, mock_llm_service):
        """Test chat completion when LLM service is unavailable."""
        mock_llm_service.is_available.return_value = False
        
        response = client.post(
            "/api/v1/chats/completions",
            json={
                "message": "Test message",
                "model": "gpt-4",
            },
        )
        
        assert response.status_code == 503
        assert "not available" in response.json()["detail"].lower()
    
    @patch("app.api.v1.endpoints.chats.StreamingResponse")
    def test_chat_completion_stream(self, mock_streaming_response, mock_supabase, mock_llm_service):
        """Test streaming chat completion."""
        chat_id = "stream-chat-id"
        
        # Mock chat exists check
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "user_id": mock_user["id"],
            "title": "Stream Chat",
            "model_used": "gpt-4",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }]
        
        # Mock previous messages (empty for new conversation)
        mock_supabase._client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        
        # Mock streaming response
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = ["Hello", " ", "world", "!"]
        mock_llm_service.chat_completion_stream.return_value = mock_stream
        
        # Mock message insert
        mock_supabase._client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "stream-msg-id",
            "chat_id": chat_id,
            "role": "assistant",
            "content": "",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {"streaming": True},
            "model": "gpt-4",
        }]
        
        # Mock message update
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": "stream-msg-id",
            "content": "Hello world!",
            "metadata": {"streaming": False},
        }]
        
        # Mock chat update
        mock_supabase._client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "id": chat_id,
            "updated_at": "2024-01-01T00:00:01",
        }]
        
        # Mock StreamingResponse
        mock_streaming_response_instance = MagicMock()
        mock_streaming_response.return_value = mock_streaming_response_instance
        
        response = client.post(
            "/api/v1/chats/completions/stream",
            json={
                "message": "Hello",
                "chat_id": chat_id,
                "model": "gpt-4",
                "stream": True,
            },
        )
        
        # Since we're mocking StreamingResponse, we just verify the function was called
        mock_streaming_response.assert_called_once()
        
        # Note: We can't easily test the streaming response with TestClient
        # In a real test, you'd use an async test client