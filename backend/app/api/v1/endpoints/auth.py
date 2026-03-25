"""
Authentication endpoints for user registration, login, and password reset.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.core.supabase import SupabaseClient

router = APIRouter()
security = HTTPBearer()


# Request/Response models
class SignUpRequest(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class SignInRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response model for authentication endpoints."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """Response model for user info."""
    id: str
    email: str
    role: str | None = None
    app_metadata: Dict[str, Any] | None = None
    user_metadata: Dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ForgotPasswordRequest(BaseModel):
    """Request model for password reset email."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(request: SignUpRequest) -> AuthResponse:
    """
    Register a new user.

    Returns:
        AuthResponse with access token and user data.
    """
    supabase = SupabaseClient()
    try:
        response = await supabase.sign_up(request.email, request.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )

    # Supabase response structure: session contains access_token, refresh_token, user
    session = response.get("session")
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No session returned from Supabase",
        )

    return AuthResponse(
        access_token=session.get("access_token"),
        token_type="bearer",
        expires_in=session.get("expires_in", 3600),
        refresh_token=session.get("refresh_token"),
        user=response.get("user", {}),
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: SignInRequest) -> AuthResponse:
    """
    Authenticate an existing user.

    Returns:
        AuthResponse with access token and user data.
    """
    supabase = SupabaseClient()
    try:
        response = await supabase.sign_in(request.email, request.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    session = response.get("session")
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No session returned from Supabase",
        )

    return AuthResponse(
        access_token=session.get("access_token"),
        token_type="bearer",
        expires_in=session.get("expires_in", 3600),
        refresh_token=session.get("refresh_token"),
        user=response.get("user", {}),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(token: str = Depends(security)) -> MessageResponse:
    """
    Log out the current user (invalidate token on client side).
    Supabase tokens are stateless; we cannot invalidate them server-side
    without additional configuration. This endpoint is a placeholder.
    """
    # In a real implementation, you might add token to a blacklist or call Supabase sign_out.
    # For now, we just return success.
    supabase = SupabaseClient()
    try:
        await supabase.sign_out()
    except Exception:
        # Ignore errors (e.g., no session)
        pass
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(security)) -> UserResponse:
    """
    Get current authenticated user information.
    """
    supabase = SupabaseClient()
    user = await supabase.get_current_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return UserResponse(
        id=user.get("id"),
        email=user.get("email"),
        role=user.get("role"),
        app_metadata=user.get("app_metadata"),
        user_metadata=user.get("user_metadata"),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest) -> MessageResponse:
    """
    Send password reset email to user.
    """
    supabase = SupabaseClient()
    try:
        await supabase.reset_password_for_email(request.email)
    except Exception as e:
        # For security, don't reveal if email exists or not
        logger = logging.getLogger(__name__)
        logger.warning(f"Password reset request failed for {request.email}: {e}")
        # Still return success to prevent email enumeration
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest) -> MessageResponse:
    """
    Reset password using token from email.
    """
    # The token is a Supabase recovery token.
    # Supabase Python client doesn't have a direct method to reset password with token.
    # We'll need to use the auth.api.update_user with the token.
    # For now, we'll implement a placeholder that returns an error.
    # TODO: Implement proper token verification and password update.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset via token is not yet implemented. Use the frontend flow.",
    )