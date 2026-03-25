"""
API key management endpoints for storing and managing third-party API keys.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.encryption import encryption_service
from app.core.supabase import SupabaseClient

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class APIKeyCreate(BaseModel):
    """Request model for creating an API key."""
    provider: str = Field(..., description="API provider (openai, anthropic, google, azure, other)")
    api_key: str = Field(..., description="The API key to store (will be encrypted)")
    is_active: bool = Field(True, description="Whether the key is active")


class APIKeyUpdate(BaseModel):
    """Request model for updating an API key."""
    api_key: Optional[str] = Field(None, description="New API key (will be encrypted)")
    is_active: Optional[bool] = Field(None, description="Whether the key is active")


class APIKeyResponse(BaseModel):
    """Response model for API key."""
    id: str
    user_id: str
    provider: str
    masked_key: str
    is_active: bool
    created_at: str
    updated_at: str


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys."""
    api_keys: List[APIKeyResponse]
    total: int


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all API keys for the current user.
    
    Returns a list of API keys (with masked values) for the authenticated user.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Fetch API keys from database
        result = supabase._client.table("api_keys").select("*").eq("user_id", user_id).execute()
        
        api_keys = []
        for key in result.data:
            # Decrypt to get masked version
            try:
                masked = encryption_service._mask_api_key(
                    encryption_service.decrypt(key["encrypted_key"])
                )
            except Exception:
                masked = "***"
            
            api_keys.append({
                "id": key["id"],
                "user_id": key["user_id"],
                "provider": key["provider"],
                "masked_key": masked,
                "is_active": key["is_active"],
                "created_at": key["created_at"],
                "updated_at": key["updated_at"],
            })
        
        return {
            "api_keys": api_keys,
            "total": len(api_keys),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys",
        )


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a new API key.
    
    Stores an encrypted API key for the authenticated user.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Validate provider
        valid_providers = ["openai", "anthropic", "google", "azure", "other"]
        if api_key_data.provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}",
            )
        
        # Check if user already has a key for this provider
        existing = supabase._client.table("api_keys").select("*").eq("user_id", user_id).eq("provider", api_key_data.provider).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"API key already exists for provider: {api_key_data.provider}",
            )
        
        # Encrypt the API key
        encrypted_data = encryption_service.encrypt_api_key(
            api_key_data.api_key,
            api_key_data.provider
        )
        
        # Prepare data for insertion
        key_data = {
            "user_id": user_id,
            "provider": api_key_data.provider,
            "encrypted_key": encrypted_data["encrypted_key"],
            "is_active": api_key_data.is_active,
        }
        
        # Insert into database
        result = supabase._client.table("api_keys").insert(key_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key",
            )
        
        created_key = result.data[0]
        
        return {
            "id": created_key["id"],
            "user_id": created_key["user_id"],
            "provider": created_key["provider"],
            "masked_key": encrypted_data["masked_key"],
            "is_active": created_key["is_active"],
            "created_at": created_key["created_at"],
            "updated_at": created_key["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a specific API key by ID.
    
    Returns API key details (with masked value) for the authenticated user.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Fetch API key
        result = supabase._client.table("api_keys").select("*").eq("id", key_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        
        key = result.data[0]
        
        # Decrypt to get masked version
        try:
            masked = encryption_service._mask_api_key(
                encryption_service.decrypt(key["encrypted_key"])
            )
        except Exception:
            masked = "***"
        
        return {
            "id": key["id"],
            "user_id": key["user_id"],
            "provider": key["provider"],
            "masked_key": masked,
            "is_active": key["is_active"],
            "created_at": key["created_at"],
            "updated_at": key["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch API key",
        )


@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    api_key_update: APIKeyUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update an API key.
    
    Updates either the API key value or its active status.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Check if key exists and belongs to user
        existing = supabase._client.table("api_keys").select("*").eq("id", key_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        
        # Prepare update data
        update_data = {}
        if api_key_update.api_key is not None:
            # Encrypt the new API key
            key = existing.data[0]
            encrypted_data = encryption_service.encrypt_api_key(
                api_key_update.api_key,
                key["provider"]
            )
            update_data["encrypted_key"] = encrypted_data["encrypted_key"]
        
        if api_key_update.is_active is not None:
            update_data["is_active"] = api_key_update.is_active
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )
        
        # Update the key
        result = supabase._client.table("api_keys").update(update_data).eq("id", key_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update API key",
            )
        
        updated_key = result.data[0]
        
        # Get masked version
        try:
            masked = encryption_service._mask_api_key(
                encryption_service.decrypt(updated_key["encrypted_key"])
            )
        except Exception:
            masked = "***"
        
        return {
            "id": updated_key["id"],
            "user_id": updated_key["user_id"],
            "provider": updated_key["provider"],
            "masked_key": masked,
            "is_active": updated_key["is_active"],
            "created_at": updated_key["created_at"],
            "updated_at": updated_key["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key",
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """
    Delete an API key.
    
    Permanently deletes an API key for the authenticated user.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Check if key exists and belongs to user
        existing = supabase._client.table("api_keys").select("*").eq("id", key_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        
        # Delete the key
        supabase._client.table("api_keys").delete().eq("id", key_id).eq("user_id", user_id).execute()
        
        # Return 204 No Content
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key",
        )


@router.get("/provider/{provider}", response_model=Optional[APIKeyResponse])
async def get_api_key_by_provider(
    provider: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Optional[Dict[str, Any]]:
    """
    Get API key for a specific provider.
    
    Returns the API key (with masked value) for the specified provider.
    Returns null if no key exists for that provider.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Fetch API key for provider
        result = supabase._client.table("api_keys").select("*").eq("user_id", user_id).eq("provider", provider).execute()
        
        if not result.data:
            return None
        
        key = result.data[0]
        
        # Decrypt to get masked version
        try:
            masked = encryption_service._mask_api_key(
                encryption_service.decrypt(key["encrypted_key"])
            )
        except Exception:
            masked = "***"
        
        return {
            "id": key["id"],
            "user_id": key["user_id"],
            "provider": key["provider"],
            "masked_key": masked,
            "is_active": key["is_active"],
            "created_at": key["created_at"],
            "updated_at": key["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching API key by provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch API key",
        )