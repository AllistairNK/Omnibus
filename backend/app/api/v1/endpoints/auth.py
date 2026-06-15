"""
Authentication endpoints for user registration, login, and password reset.
"""
import logging
from typing import Any, Dict, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.core.supabase import SupabaseClient
from app.core.auth import ensure_user_exists

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


# ── Request/Response models ────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: Dict[str, Any]


class SignUpPendingResponse(BaseModel):
    message: str
    requires_confirmation: bool = True


class UserResponse(BaseModel):
    id: str
    email: str
    role: str | None = None
    app_metadata: Dict[str, Any] | None = None
    user_metadata: Dict[str, Any] | None = None


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_user_custom_role(user_id: str) -> str:
    """Fetch custom role from users table."""
    try:
        supabase = SupabaseClient()
        result = supabase.client.table("users").select("role").eq("id", user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("role", "user")
    except Exception as e:
        logger.warning(f"Failed to fetch custom role for user {user_id}: {e}")
    return "user"

def _serialize_user(user) -> Dict[str, Any]:
    """Convert a supabase-py v2 User object to a plain dict."""
    if user is None:
        return {}
    
    # Get custom role from users table
    custom_role = _get_user_custom_role(str(user.id))
    
    return {
        "id": str(user.id),
        "email": user.email,
        "role": custom_role,  # Use custom role from users table, not Supabase auth role
        "app_metadata": user.app_metadata or {},
        "user_metadata": user.user_metadata or {},
    }


def _build_auth_response(session, user) -> AuthResponse:
    """Build AuthResponse from supabase-py v2 session/user objects."""
    return AuthResponse(
        access_token=session.access_token,
        token_type="bearer",
        expires_in=session.expires_in or 3600,
        refresh_token=session.refresh_token,
        user=_serialize_user(user),
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/signup",
    response_model=Union[AuthResponse, SignUpPendingResponse],
    status_code=status.HTTP_201_CREATED,
)
async def sign_up(request: SignUpRequest) -> Union[AuthResponse, SignUpPendingResponse]:
    supabase = SupabaseClient()
    try:
        response = supabase.client.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )

    # Email confirmation enabled → session is None until user confirms
    if response.session is None:
        # Even if email confirmation is required, we should create the user record
        if response.user and hasattr(response.user, 'id'):
            try:
                await ensure_user_exists(str(response.user.id), response.user.email)
            except Exception as e:
                logger.warning(f"Failed to create user record during signup: {e}")
        
        return SignUpPendingResponse(
            message="Registration successful. Please check your email to confirm your account."
        )

    # Create user record in our database
    if response.user and hasattr(response.user, 'id'):
        try:
            await ensure_user_exists(str(response.user.id), response.user.email)
        except Exception as e:
            logger.warning(f"Failed to create user record during signup: {e}")

    return _build_auth_response(response.session, response.user)


@router.post("/login", response_model=AuthResponse)
async def login(request: SignInRequest) -> AuthResponse:
    supabase = SupabaseClient()
    try:
        response = supabase.client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if response.session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed: no session returned.",
        )

    return _build_auth_response(response.session, response.user)


@router.post("/logout", response_model=MessageResponse)
async def logout(token: str = Depends(security)) -> MessageResponse:
    supabase = SupabaseClient()
    try:
        supabase.client.auth.sign_out()
    except Exception:
        pass
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(security)) -> UserResponse:
    supabase = SupabaseClient()
    try:
        response = supabase.client.auth.get_user()
        user = response.user if response else None
    except Exception:
        user = None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Get custom role from users table
    custom_role = _get_user_custom_role(str(user.id))

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=custom_role,  # Use custom role from users table
        app_metadata=user.app_metadata,
        user_metadata=user.user_metadata,
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest) -> MessageResponse:
    supabase = SupabaseClient()
    try:
        supabase.client.auth.reset_password_for_email(request.email)
    except Exception as e:
        logger.warning(f"Password reset request failed for {request.email}: {e}")
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest) -> MessageResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset via token is not yet implemented.",
    )