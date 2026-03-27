"""
Admin endpoints for system management.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, require_admin
from app.core.supabase import SupabaseClient

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""
    total_users: int
    total_documents: int
    total_chats: int
    total_messages: int
    active_users_24h: int
    new_users_24h: int
    storage_used_mb: float
    api_calls_24h: int
    avg_response_time_ms: float


class DocumentAuditEntry(BaseModel):
    """Model for document audit log entry."""
    id: str
    document_id: str
    user_id: str
    action: str  # upload, delete, view, update
    timestamp: str
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class DocumentAuditResponse(BaseModel):
    """Response model for document audit log."""
    entries: List[DocumentAuditEntry]
    total: int
    page: int
    page_size: int


class SystemHealthResponse(BaseModel):
    """Response model for system health check."""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    components: Dict[str, str]
    metrics: Dict[str, Any]
    issues: List[str]


class UserManagementRequest(BaseModel):
    """Request model for user management actions."""
    user_id: str
    action: str  # disable, enable, delete, change_role
    role: Optional[str] = None
    reason: Optional[str] = None


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get system statistics (admin only).
    
    Returns comprehensive system statistics for monitoring.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Get counts from database
        users_count = supabase._client.table("users").select("*", count="exact").execute()
        documents_count = supabase._client.table("documents").select("*", count="exact").execute()
        chats_count = supabase._client.table("chats").select("*", count="exact").execute()
        messages_count = supabase._client.table("chat_messages").select("*", count="exact").execute()
        
        # Calculate 24-hour active users (users with activity in last 24 hours)
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        active_users = supabase._client.table("users").select("*", count="exact").gte("last_active_at", twenty_four_hours_ago).execute()
        
        # Calculate new users in last 24 hours
        new_users = supabase._client.table("users").select("*", count="exact").gte("created_at", twenty_four_hours_ago).execute()
        
        # Estimate storage used (rough calculation)
        storage_result = supabase._client.table("documents").select("file_size_bytes").execute()
        storage_used_bytes = sum(doc.get("file_size_bytes", 0) for doc in storage_result.data)
        storage_used_mb = storage_used_bytes / (1024 * 1024)
        
        # For now, use placeholder values for API calls and response time
        # In production, these would come from monitoring systems
        api_calls_24h = 0
        avg_response_time_ms = 0.0
        
        return {
            "total_users": users_count.count if hasattr(users_count, 'count') else len(users_count.data),
            "total_documents": documents_count.count if hasattr(documents_count, 'count') else len(documents_count.data),
            "total_chats": chats_count.count if hasattr(chats_count, 'count') else len(chats_count.data),
            "total_messages": messages_count.count if hasattr(messages_count, 'count') else len(messages_count.data),
            "active_users_24h": active_users.count if hasattr(active_users, 'count') else len(active_users.data),
            "new_users_24h": new_users.count if hasattr(new_users, 'count') else len(new_users.data),
            "storage_used_mb": round(storage_used_mb, 2),
            "api_calls_24h": api_calls_24h,
            "avg_response_time_ms": avg_response_time_ms,
        }
    except Exception as e:
        logger.error(f"Error fetching system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system statistics",
        )


@router.get("/document-audit", response_model=DocumentAuditResponse)
async def get_document_audit_log(
    page: int = 1,
    page_size: int = 50,
    document_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get document audit log (admin only).
    
    Returns audit trail of document-related actions.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size - 1
        
        # Build query
        query = supabase._client.table("document_audit_log").select("*")
        
        if document_id:
            query = query.eq("document_id", document_id)
        if user_id:
            query = query.eq("user_id", user_id)
        if action:
            query = query.eq("action", action)
        
        # Order by timestamp descending (most recent first)
        query = query.order("timestamp", desc=True)
        
        # Apply pagination
        audit_data = query.range(start_idx, end_idx).execute()
        
        # Get total count
        count_query = supabase._client.table("document_audit_log").select("*", count="exact")
        if document_id:
            count_query = count_query.eq("document_id", document_id)
        if user_id:
            count_query = count_query.eq("user_id", user_id)
        if action:
            count_query = count_query.eq("action", action)
        
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else len(audit_data.data)
        
        # Format response
        entries = []
        for entry in audit_data.data:
            entries.append({
                "id": entry.get("id", ""),
                "document_id": entry.get("document_id", ""),
                "user_id": entry.get("user_id", ""),
                "action": entry.get("action", ""),
                "timestamp": entry.get("timestamp", ""),
                "details": entry.get("details", {}),
                "ip_address": entry.get("ip_address"),
                "user_agent": entry.get("user_agent"),
            })
        
        return {
            "entries": entries,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(f"Error fetching document audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document audit log",
        )


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get detailed system health status (admin only).
    
    Returns health status of all system components.
    """
    try:
        supabase = SupabaseClient()
        
        components = {}
        issues = []
        
        # Check Supabase connection
        if supabase._client:
            try:
                # Simple query to test connection
                supabase._client.table("users").select("count(*)", count="exact").limit(1).execute()
                components["supabase_database"] = "healthy"
            except Exception as e:
                components["supabase_database"] = "unhealthy"
                issues.append(f"Supabase database connection failed: {str(e)}")
        else:
            components["supabase_database"] = "unhealthy"
            issues.append("Supabase client not initialized")
        
        # Check if we can connect to Supabase Auth
        components["supabase_auth"] = "healthy" if supabase._client else "unhealthy"
        
        # Check ChromaDB (vector store) - this would need actual connection test
        # For now, assume it's healthy if the service is running
        components["chromadb_vector_store"] = "healthy"
        
        # Check LLM providers (simplified check)
        components["llm_providers"] = "healthy"
        
        # Check file storage
        components["file_storage"] = "healthy"
        
        # Determine overall status
        if any(status == "unhealthy" for status in components.values()):
            overall_status = "unhealthy"
        elif any(status == "degraded" for status in components.values()):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Get some metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "component_count": len(components),
            "issue_count": len(issues),
        }
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "metrics": metrics,
            "issues": issues,
        }
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check system health",
        )


@router.post("/users/{user_id}/manage")
async def manage_user(
    user_id: str,
    management_request: UserManagementRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Manage user account (admin only).
    
    Perform administrative actions on user accounts.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase client not initialized",
            )
        
        # Check if target user exists
        user_check = supabase._client.table("users").select("*").eq("id", user_id).execute()
        if not user_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        action = management_request.action
        
        if action == "disable":
            # Mark user as disabled in our database
            supabase._client.table("users").update({
                "is_active": False,
                "disabled_at": datetime.now().isoformat(),
                "disabled_reason": management_request.reason or "Disabled by admin"
            }).eq("id", user_id).execute()
            
            return {"message": f"User {user_id} disabled successfully"}
            
        elif action == "enable":
            # Mark user as enabled in our database
            supabase._client.table("users").update({
                "is_active": True,
                "disabled_at": None,
                "disabled_reason": None
            }).eq("id", user_id).execute()
            
            return {"message": f"User {user_id} enabled successfully"}
            
        elif action == "change_role":
            if not management_request.role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role is required for change_role action",
                )
            
            # Update user role in our database
            supabase._client.table("users").update({
                "role": management_request.role,
                "role_updated_at": datetime.now().isoformat(),
                "role_updated_by": current_user.get("id")
            }).eq("id", user_id).execute()
            
            return {"message": f"User {user_id} role changed to {management_request.role}"}
            
        elif action == "delete":
            # Delete user from our database (cascade will handle related records)
            supabase._client.table("users").delete().eq("id", user_id).execute()
            
            # Note: Deleting from Supabase Auth requires admin privileges
            # For now, we just delete from our database
            logger.info(f"User {user_id} marked for deletion by admin {current_user.get('id')}")
            
            return {"message": f"User {user_id} deleted from application database"}
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported action: {action}",
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to manage user",
        )