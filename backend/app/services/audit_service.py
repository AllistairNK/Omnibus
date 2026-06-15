"""
Document audit logging service.

Provides helper functions to log document-related actions (upload, delete, view, update)
to the document_audit_log table in Supabase, and to query the audit log.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.supabase import SupabaseClient

logger = logging.getLogger(__name__)

# Valid action types
VALID_ACTIONS = {"upload", "delete", "view", "update"}


async def log_document_action(
    document_id: str,
    user_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Log a document-related action to the audit trail.

    Args:
        document_id: The UUID of the document acted upon.
        user_id: The UUID of the user who performed the action.
        action: One of 'upload', 'delete', 'view', 'update'.
        details: Optional JSON-serializable dict with extra context.
        ip_address: Optional client IP address.
        user_agent: Optional client user-agent string.

    Returns:
        The created audit log entry dict, or None if logging failed.
    """
    if action not in VALID_ACTIONS:
        logger.warning(f"Invalid audit action '{action}'. Must be one of {VALID_ACTIONS}")
        return None

    try:
        supabase = SupabaseClient()
        if not supabase._client:
            logger.warning("Supabase client not initialized, cannot log audit entry")
            return None

        entry = {
            "document_id": document_id,
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        result = supabase._client.table("document_audit_log").insert(entry).execute()
        if result.data:
            logger.debug(f"Audit log entry created: {action} on document {document_id}")
            return result.data[0]
        else:
            logger.warning(f"Audit log insert returned no data for {action} on {document_id}")
            return None

    except Exception as e:
        logger.error(f"Failed to log audit entry: {e}")
        return None


async def get_document_audit_log(
    page: int = 1,
    page_size: int = 50,
    document_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query the document audit log with pagination and optional filters.

    Args:
        page: Page number (1-indexed).
        page_size: Number of entries per page.
        document_id: Optional filter by document ID.
        user_id: Optional filter by user ID.
        action: Optional filter by action type.

    Returns:
        Dict with 'entries', 'total', 'page', 'page_size'.
    """
    try:
        supabase = SupabaseClient()
        if not supabase._client:
            logger.warning("Supabase client not initialized, returning empty audit log")
            return {"entries": [], "total": 0, "page": page, "page_size": page_size}

        # Build the query
        query = supabase._client.table("document_audit_log").select("*", count="exact")

        # Apply optional filters
        if document_id:
            query = query.eq("document_id", document_id)
        if user_id:
            query = query.eq("user_id", user_id)
        if action:
            query = query.eq("action", action)

        # Apply ordering (most recent first) and pagination
        offset = (page - 1) * page_size
        query = query.order("timestamp", desc=True).range(offset, offset + page_size - 1)

        result = query.execute()

        entries = result.data if result.data else []
        total = result.count if hasattr(result, "count") else len(entries)

        return {
            "entries": entries,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    except Exception as e:
        logger.error(f"Failed to query document audit log: {e}")
        return {"entries": [], "total": 0, "page": page, "page_size": page_size}
