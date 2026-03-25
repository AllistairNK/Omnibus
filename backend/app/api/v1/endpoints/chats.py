"""
Chat session and message management endpoints.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.database import db
from app.core.supabase import SupabaseClient

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class ChatCreate(BaseModel):
    """Request model for creating a new chat."""
    title: Optional[str] = Field(None, max_length=255, description="Chat title")
    model_used: Optional[str] = Field(None, max_length=100, description="Model to use for this chat")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ChatUpdate(BaseModel):
    """Request model for updating a chat."""
    title: Optional[str] = Field(None, max_length=255, description="Chat title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response model for chat session."""
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    model_used: Optional[str] = None
    metadata: Dict[str, Any] = {}
    message_count: Optional[int] = 0


class ChatListResponse(BaseModel):
    """Response model for listing chats."""
    chats: List[ChatResponse]
    total: int
    page: int
    page_size: int


class MessageCreate(BaseModel):
    """Request model for creating a message."""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tokens_used: Optional[int] = Field(None, description="Token count for this message")
    model: Optional[str] = Field(None, description="Model that generated this message")


class MessageResponse(BaseModel):
    """Response model for message."""
    id: str
    chat_id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}
    tokens_used: Optional[int] = None
    model: Optional[str] = None


class MessageListResponse(BaseModel):
    """Response model for listing messages."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion (basic LLM integration)."""
    message: str = Field(..., description="User message to send to LLM")
    chat_id: Optional[str] = Field(None, description="Existing chat ID to continue conversation")
    model: Optional[str] = Field(None, description="Model to use for completion")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion."""
    chat_id: str
    message_id: str
    role: str = "assistant"
    content: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    timestamp: str


# Chat session management endpoints
@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_create: ChatCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a new chat session.
    
    Creates a new chat session for the authenticated user.
    """
    try:
        chat_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Use Supabase client for database operations
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Insert chat into database
        chat_data = {
            "id": chat_id,
            "user_id": current_user["id"],
            "title": chat_create.title or "New Chat",
            "model_used": chat_create.model_used,
            "metadata": chat_create.metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        
        result = supabase._client.table("chats").insert(chat_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat",
            )
        
        return {
            "id": chat_id,
            "user_id": current_user["id"],
            "title": chat_data["title"],
            "created_at": now,
            "updated_at": now,
            "model_used": chat_create.model_used,
            "metadata": chat_create.metadata or {},
            "message_count": 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat",
        )


@router.get("/", response_model=ChatListResponse)
async def list_chats(
    page: int = 1,
    page_size: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List chat sessions for the current user.
    
    Returns paginated list of chat sessions ordered by most recent.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get chats for current user
        query = (
            supabase._client.table("chats")
            .select("*", count="exact")
            .eq("user_id", current_user["id"])
            .order("updated_at", desc=True)
            .range(offset, offset + page_size - 1)
        )
        
        result = query.execute()
        
        # Get message counts for each chat
        chats_with_counts = []
        for chat in result.data:
            # Count messages for this chat
            msg_count_result = (
                supabase._client.table("messages")
                .select("*", count="exact")
                .eq("chat_id", chat["id"])
                .execute()
            )
            
            chats_with_counts.append({
                "id": chat["id"],
                "user_id": chat["user_id"],
                "title": chat["title"],
                "created_at": chat["created_at"],
                "updated_at": chat["updated_at"],
                "model_used": chat.get("model_used"),
                "metadata": chat.get("metadata", {}),
                "message_count": msg_count_result.count or 0,
            })
        
        return {
            "chats": chats_with_counts,
            "total": result.count or 0,
            "page": page,
            "page_size": page_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing chats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list chats",
        )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a specific chat session.
    
    Returns chat details including message count.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get chat
        result = (
            supabase._client.table("chats")
            .select("*")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        chat = result.data[0]
        
        # Count messages
        msg_count_result = (
            supabase._client.table("messages")
            .select("*", count="exact")
            .eq("chat_id", chat_id)
            .execute()
        )
        
        return {
            "id": chat["id"],
            "user_id": chat["user_id"],
            "title": chat["title"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"],
            "model_used": chat.get("model_used"),
            "metadata": chat.get("metadata", {}),
            "message_count": msg_count_result.count or 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat",
        )


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    chat_update: ChatUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update a chat session.
    
    Updates chat title and metadata.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if chat exists and belongs to user
        check_result = (
            supabase._client.table("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not check_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if chat_update.title is not None:
            update_data["title"] = chat_update.title
        if chat_update.metadata is not None:
            update_data["metadata"] = chat_update.metadata
        
        # Update chat
        result = (
            supabase._client.table("chats")
            .update(update_data)
            .eq("id", chat_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update chat",
            )
        
        updated_chat = result.data[0]
        
        # Count messages
        msg_count_result = (
            supabase._client.table("messages")
            .select("*", count="exact")
            .eq("chat_id", chat_id)
            .execute()
        )
        
        return {
            "id": updated_chat["id"],
            "user_id": updated_chat["user_id"],
            "title": updated_chat["title"],
            "created_at": updated_chat["created_at"],
            "updated_at": updated_chat["updated_at"],
            "model_used": updated_chat.get("model_used"),
            "metadata": updated_chat.get("metadata", {}),
            "message_count": msg_count_result.count or 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat",
        )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """
    Delete a chat session.
    
    Deletes the chat and all associated messages (cascade delete).
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if chat exists and belongs to user
        check_result = (
            supabase._client.table("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not check_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Delete chat (messages will be cascade deleted)
        supabase._client.table("chats").delete().eq("id", chat_id).execute()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat",
        )


# Message management endpoints
@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    chat_id: str,
    message_create: MessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a new message in a chat.
    
    Adds a message to an existing chat session.
    """
    try:
        # Validate role
        if message_create.role not in ["user", "assistant", "system"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'user', 'assistant', or 'system'",
            )
        
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if chat exists and belongs to user
        chat_result = (
            supabase._client.table("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not chat_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Create message
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        message_data = {
            "id": message_id,
            "chat_id": chat_id,
            "role": message_create.role,
            "content": message_create.content,
            "timestamp": now,
            "metadata": message_create.metadata or {},
            "tokens_used": message_create.tokens_used,
            "model": message_create.model,
        }
        
        result = supabase._client.table("messages").insert(message_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create message",
            )
        
        # Update chat's updated_at timestamp
        supabase._client.table("chats").update({
            "updated_at": now
        }).eq("id", chat_id).execute()
        
        return {
            "id": message_id,
            "chat_id": chat_id,
            "role": message_create.role,
            "content": message_create.content,
            "timestamp": now,
            "metadata": message_create.metadata or {},
            "tokens_used": message_create.tokens_used,
            "model": message_create.model,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message",
        )


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def list_messages(
    chat_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List messages in a chat.
    
    Returns paginated list of messages in chronological order.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if chat exists and belongs to user
        chat_result = (
            supabase._client.table("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not chat_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get messages
        query = (
            supabase._client.table("messages")
            .select("*", count="exact")
            .eq("chat_id", chat_id)
            .order("timestamp", desc=False)  # Oldest first
            .range(offset, offset + page_size - 1)
        )
        
        result = query.execute()
        
        return {
            "messages": result.data,
            "total": result.count or 0,
            "page": page,
            "page_size": page_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list messages",
        )


@router.get("/{chat_id}/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    chat_id: str,
    message_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a specific message.
    
    Returns message details.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if chat exists and belongs to user
        chat_result = (
            supabase._client.table("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not chat_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Get message
        result = (
            supabase._client.table("messages")
            .select("*")
            .eq("id", message_id)
            .eq("chat_id", chat_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get message",
        )


@router.delete("/{chat_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    chat_id: str,
    message_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """
    Delete a message.
    
    Removes a message from a chat.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if chat exists and belongs to user
        chat_result = (
            supabase._client.table("chats")
            .select("id")
            .eq("id", chat_id)
            .eq("user_id", current_user["id"])
            .execute()
        )
        
        if not chat_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Check if message exists
        message_result = (
            supabase._client.table("messages")
            .select("id")
            .eq("id", message_id)
            .eq("chat_id", chat_id)
            .execute()
        )
        
        if not message_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        # Delete message
        supabase._client.table("messages").delete().eq("id", message_id).execute()
        
        # Update chat's updated_at timestamp
        supabase._client.table("chats").update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", chat_id).execute()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message",
        )


# Chat completion endpoint (basic LLM integration)
@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    completion_request: ChatCompletionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a chat completion using LLM.
    
    Sends a user message to the LLM and returns the assistant's response.
    Creates or uses an existing chat session.
    """
    try:
        from app.services.llm_service import llm_service
        
        # Initialize LLM service if needed
        if not llm_service._initialized:
            await llm_service.initialize()
        
        if not await llm_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service not available",
            )
        
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        chat_id = completion_request.chat_id
        now = datetime.utcnow().isoformat()
        
        # Get or create chat
        if chat_id:
            # Check if chat exists and belongs to user
            chat_result = (
                supabase._client.table("chats")
                .select("*")
                .eq("id", chat_id)
                .eq("user_id", current_user["id"])
                .execute()
            )
            
            if not chat_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat not found",
                )
            
            chat = chat_result.data[0]
            
            # Get previous messages for context
            messages_result = (
                supabase._client.table("messages")
                .select("*")
                .eq("chat_id", chat_id)
                .order("timestamp", desc=False)
                .limit(20)  # Limit context window
                .execute()
            )
            
            previous_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages_result.data
            ]
        else:
            # Create new chat
            chat_id = str(uuid.uuid4())
            chat_data = {
                "id": chat_id,
                "user_id": current_user["id"],
                "title": completion_request.message[:50] + "..." if len(completion_request.message) > 50 else completion_request.message,
                "model_used": completion_request.model,
                "created_at": now,
                "updated_at": now,
            }
            
            supabase._client.table("chats").insert(chat_data).execute()
            chat = chat_data
            previous_messages = []
        
        # Add user message to chat history
        user_message_id = str(uuid.uuid4())
        user_message_data = {
            "id": user_message_id,
            "chat_id": chat_id,
            "role": "user",
            "content": completion_request.message,
            "timestamp": now,
            "model": completion_request.model,
        }
        
        supabase._client.table("messages").insert(user_message_data).execute()
        
        # Prepare messages for LLM
        llm_messages = previous_messages + [
            {"role": "user", "content": completion_request.message}
        ]
        
        # Get LLM response
        llm_response = await llm_service.chat_completion(
            messages=llm_messages,
            model=completion_request.model,
            temperature=completion_request.temperature,
            max_tokens=completion_request.max_tokens,
            stream=False,  # Non-streaming for this endpoint
        )
        
        # Save assistant response
        assistant_message_id = str(uuid.uuid4())
        assistant_message_data = {
            "id": assistant_message_id,
            "chat_id": chat_id,
            "role": llm_response["role"],
            "content": llm_response["content"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {},
            "tokens_used": llm_response.get("tokens_used"),
            "model": llm_response.get("model"),
        }
        
        supabase._client.table("messages").insert(assistant_message_data).execute()
        
        # Update chat's updated_at timestamp
        supabase._client.table("chats").update({
            "updated_at": datetime.utcnow().isoformat(),
            "model_used": completion_request.model or chat.get("model_used"),
        }).eq("id", chat_id).execute()
        
        return {
            "chat_id": chat_id,
            "message_id": assistant_message_id,
            "role": llm_response["role"],
            "content": llm_response["content"],
            "model": llm_response.get("model"),
            "tokens_used": llm_response.get("tokens_used"),
            "timestamp": assistant_message_data["timestamp"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat completion",
        )


# Streaming chat completion endpoint
@router.post("/completions/stream")
async def create_chat_completion_stream(
    completion_request: ChatCompletionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create a streaming chat completion using LLM.
    
    Streams the assistant's response using Server-Sent Events (SSE).
    """
    from fastapi.responses import StreamingResponse
    import json
    
    try:
        from app.services.llm_service import llm_service
        
        # Initialize LLM service if needed
        if not llm_service._initialized:
            await llm_service.initialize()
        
        if not await llm_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service not available",
            )
        
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        chat_id = completion_request.chat_id
        now = datetime.utcnow().isoformat()
        
        # Get or create chat
        if chat_id:
            # Check if chat exists and belongs to user
            chat_result = (
                supabase._client.table("chats")
                .select("*")
                .eq("id", chat_id)
                .eq("user_id", current_user["id"])
                .execute()
            )
            
            if not chat_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat not found",
                )
            
            chat = chat_result.data[0]
            
            # Get previous messages for context
            messages_result = (
                supabase._client.table("messages")
                .select("*")
                .eq("chat_id", chat_id)
                .order("timestamp", desc=False)
                .limit(20)  # Limit context window
                .execute()
            )
            
            previous_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages_result.data
            ]
        else:
            # Create new chat
            chat_id = str(uuid.uuid4())
            chat_data = {
                "id": chat_id,
                "user_id": current_user["id"],
                "title": completion_request.message[:50] + "..." if len(completion_request.message) > 50 else completion_request.message,
                "model_used": completion_request.model,
                "created_at": now,
                "updated_at": now,
            }
            
            supabase._client.table("chats").insert(chat_data).execute()
            chat = chat_data
            previous_messages = []
        
        # Add user message to chat history
        user_message_id = str(uuid.uuid4())
        user_message_data = {
            "id": user_message_id,
            "chat_id": chat_id,
            "role": "user",
            "content": completion_request.message,
            "timestamp": now,
            "model": completion_request.model,
        }
        
        supabase._client.table("messages").insert(user_message_data).execute()
        
        # Prepare messages for LLM
        llm_messages = previous_messages + [
            {"role": "user", "content": completion_request.message}
        ]
        
        # Create assistant message record (will be updated with full content later)
        assistant_message_id = str(uuid.uuid4())
        assistant_message_data = {
            "id": assistant_message_id,
            "chat_id": chat_id,
            "role": "assistant",
            "content": "",  # Will be updated as we stream
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"streaming": True},
            "model": completion_request.model,
        }
        
        supabase._client.table("messages").insert(assistant_message_data).execute()
        
        async def event_generator():
            """Generate Server-Sent Events for streaming response."""
            full_response = ""
            
            try:
                # Stream tokens from LLM
                async for token in llm_service.chat_completion_stream(
                    messages=llm_messages,
                    model=completion_request.model,
                    temperature=completion_request.temperature,
                    max_tokens=completion_request.max_tokens,
                ):
                    full_response += token
                    
                    # Send token as SSE event
                    event_data = {
                        "type": "token",
                        "data": {
                            "token": token,
                            "message_id": assistant_message_id,
                            "chat_id": chat_id,
                        }
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                
                # Send completion event
                completion_event = {
                    "type": "complete",
                    "data": {
                        "message_id": assistant_message_id,
                        "chat_id": chat_id,
                        "full_response": full_response,
                    }
                }
                yield f"data: {json.dumps(completion_event)}\n\n"
                
                # Update assistant message with full content
                supabase._client.table("messages").update({
                    "content": full_response,
                    "metadata": {"streaming": False},
                }).eq("id", assistant_message_id).execute()
                
                # Update chat's updated_at timestamp
                supabase._client.table("chats").update({
                    "updated_at": datetime.utcnow().isoformat(),
                    "model_used": completion_request.model or chat.get("model_used"),
                }).eq("id", chat_id).execute()
                
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                # Send error event
                error_event = {
                    "type": "error",
                    "data": {
                        "message": str(e),
                        "message_id": assistant_message_id,
                        "chat_id": chat_id,
                    }
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                
                # Update message with error
                supabase._client.table("messages").update({
                    "content": f"[Streaming error: {str(e)}]",
                    "metadata": {"streaming": False, "error": str(e)},
                }).eq("id", assistant_message_id).execute()
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering for nginx
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating streaming chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create streaming chat completion",
        )