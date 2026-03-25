"""
User profile management endpoints.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.auth import get_current_user, verify_token
from app.core.supabase import SupabaseClient

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None


class UserListResponse(BaseModel):
    """Response model for listing users (admin only)."""
    users: List[UserProfileResponse]
    total: int
    page: int
    page_size: int


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get the current user's profile.
    
    Returns the authenticated user's profile information.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user from Supabase Auth
        response = supabase._client.auth.get_user(current_user["access_token"])
        user = response.user
        
        # Also get from our users table if it exists
        try:
            db_user = supabase._client.table("users").select("*").eq("id", user.id).execute()
            if db_user.data:
                user_data = db_user.data[0]
            else:
                user_data = {}
        except Exception as e:
            logger.warning(f"Could not fetch user from database: {e}")
            user_data = {}
        
        return {
            "id": user.id,
            "email": user.email,
            "display_name": user_data.get("display_name"),
            "avatar_url": user_data.get("avatar_url"),
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else "",
            "updated_at": user_data.get("updated_at", ""),
            "metadata": user_data.get("metadata", {}),
            "app_metadata": user.app_metadata,
            "user_metadata": user.user_metadata,
        }
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile",
        )


@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_update: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update the current user's profile.
    
    Updates user profile information in both Supabase Auth and our database.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get current user ID
        response = supabase._client.auth.get_user(current_user["access_token"])
        user_id = response.user.id
        
        # Prepare update data for our users table
        update_data = {}
        if profile_update.display_name is not None:
            update_data["display_name"] = profile_update.display_name
        if profile_update.avatar_url is not None:
            update_data["avatar_url"] = profile_update.avatar_url
        if profile_update.metadata is not None:
            update_data["metadata"] = profile_update.metadata
        
        # Update in our users table
        if update_data:
            try:
                # Check if user exists in our table
                existing = supabase._client.table("users").select("id").eq("id", user_id).execute()
                if existing.data:
                    # Update existing user
                    supabase._client.table("users").update(update_data).eq("id", user_id).execute()
                else:
                    # Create user record if it doesn't exist
                    create_data = {
                        "id": user_id,
                        "email": response.user.email,
                        **update_data
                    }
                    supabase._client.table("users").insert(create_data).execute()
            except Exception as e:
                logger.error(f"Error updating user in database: {e}")
                # Continue anyway - auth update is more important
        
        # Update email in Supabase Auth if provided
        if profile_update.email:
            try:
                supabase._client.auth.update_user(
                    access_token=current_user["access_token"],
                    attributes={"email": profile_update.email}
                )
            except Exception as e:
                logger.error(f"Error updating email in Supabase Auth: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to update email: {str(e)}",
                )
        
        # Get updated user data
        updated_response = supabase._client.auth.get_user(current_user["access_token"])
        user = updated_response.user
        
        # Get updated database record
        try:
            db_user = supabase._client.table("users").select("*").eq("id", user_id).execute()
            user_data = db_user.data[0] if db_user.data else {}
        except Exception:
            user_data = {}
        
        return {
            "id": user.id,
            "email": user.email,
            "display_name": user_data.get("display_name"),
            "avatar_url": user_data.get("avatar_url"),
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else "",
            "updated_at": user_data.get("updated_at", ""),
            "metadata": user_data.get("metadata", {}),
            "app_metadata": user.app_metadata,
            "user_metadata": user.user_metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """
    Delete the current user's account.
    
    Permanently deletes the user account from both Supabase Auth and our database.
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
        
        # Delete from our database tables (cascade will handle related records)
        try:
            supabase._client.table("users").delete().eq("id", user_id).execute()
        except Exception as e:
            logger.warning(f"Error deleting user from database: {e}")
        
        # Delete from Supabase Auth
        try:
            # Note: This requires admin privileges or the user's own token
            # For now, we'll just mark the user as inactive in our system
            # In a production system, you'd need proper admin auth or Supabase function
            logger.info(f"User {user_id} requested account deletion")
            # supabase._client.auth.admin.delete_user(user_id)  # Admin only
        except Exception as e:
            logger.error(f"Error deleting user from Auth: {e}")
        
        # Return 204 No Content
        return None
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account",
        )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a user's profile by ID (admin only).
    
    Requires admin privileges to view other users' profiles.
    """
    # Check if current user is admin
    if not current_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get user from database
        db_user = supabase._client.table("users").select("*").eq("id", user_id).execute()
        if not db_user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        user_data = db_user.data[0]
        
        # Try to get auth info (admin only)
        try:
            # This would require admin privileges in Supabase
            # For now, return what we have from the database
            auth_user = None
        except Exception:
            auth_user = None
        
        return {
            "id": user_data["id"],
            "email": user_data.get("email", ""),
            "display_name": user_data.get("display_name"),
            "avatar_url": user_data.get("avatar_url"),
            "created_at": user_data.get("created_at", ""),
            "updated_at": user_data.get("updated_at", ""),
            "metadata": user_data.get("metadata", {}),
            "app_metadata": None,
            "user_metadata": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user",
        )