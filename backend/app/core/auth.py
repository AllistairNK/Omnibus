"""
Authentication and authorization utilities for Supabase JWT.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.supabase import SupabaseClient

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    sub: str  # user ID
    email: str
    role: Optional[str] = None
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> tuple[TokenData, str]:
    """
    Verify Supabase JWT token and return token data along with raw token.

    Args:
        credentials: HTTP Bearer token from Authorization header.

    Returns:
        Tuple of (TokenData, raw_token): Decoded token data and raw JWT token.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Decode token using Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase tokens may not have aud
        )
        # Validate required fields
        sub = payload.get("sub")
        email = payload.get("email")
        if sub is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        token_data = TokenData(
            sub=sub,
            email=email,
            role=payload.get("role"),
            app_metadata=payload.get("app_metadata"),
            user_metadata=payload.get("user_metadata"),
        )
        return (token_data, token)
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data_and_token: tuple[TokenData, str] = Depends(verify_token),
) -> Dict[str, Any]:
    """
    Get current user from token data and optionally fetch from Supabase.

    Args:
        token_data_and_token: Tuple of (TokenData, raw_token) from verify_token.

    Returns:
        Dict containing user information including access_token.
    """
    token_data, access_token = token_data_and_token
    
    # Ensure user exists in our users table
    await ensure_user_exists(token_data.sub, token_data.email)
    
    # Get custom role from database (overrides JWT role)
    db_role = await _get_user_role_from_db(token_data.sub)
    
    # Return user info with access_token for Supabase client operations
    return {
        "id": token_data.sub,
        "email": token_data.email,
        "role": db_role,  # Use database role instead of JWT role
        "app_metadata": token_data.app_metadata,
        "user_metadata": token_data.user_metadata,
        "access_token": access_token,
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get current active user (no additional checks for now).
    Could be extended to check if user is banned, etc.
    """
    return current_user


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Require admin role for the endpoint.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


async def _get_user_role_from_db(user_id: str) -> str:
    """
    Get user role from database.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Role string ('user' or 'admin'), defaults to 'user' if not found
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            logger.warning("Supabase client not initialized, cannot fetch user role")
            return "user"
        
        result = supabase._client.table("users").select("role").eq("id", user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("role", "user")
    except Exception as e:
        logger.warning(f"Failed to fetch role for user {user_id}: {e}")
    return "user"


async def ensure_user_exists(user_id: str, email: str) -> None:
    """
    Ensure a user exists in the application's users table.
    
    This function checks if a user with the given ID exists in the users table,
    and creates a record if it doesn't exist.
    
    Args:
        user_id: The user's ID from Supabase Auth
        email: The user's email address
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            logger.warning("Supabase client not initialized, cannot ensure user exists")
            return
        
        # Check if user exists in our users table
        existing = supabase._client.table("users").select("id").eq("id", user_id).execute()
        
        if not existing.data:
            # Create user record
            create_data = {
                "id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            supabase._client.table("users").insert(create_data).execute()
            logger.info(f"Created user record for {email} ({user_id})")
        else:
            logger.debug(f"User {user_id} already exists in users table")
            
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        # Don't raise exception - this is a helper function that shouldn't break the main flow