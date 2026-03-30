"""
Document metadata endpoints for managing uploaded documents.
Note: This handles metadata only, not file upload/processing (Task 3.1).
"""
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
import traceback
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.supabase import SupabaseClient
from app.services.document_processor import DocumentProcessor

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class DocumentCreate(BaseModel):
    """Request model for creating document metadata."""
    filename: str = Field(..., max_length=255, description="Original filename")
    file_path: Optional[str] = Field(None, max_length=500, description="Path in Supabase Storage")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_type: Optional[str] = Field(None, max_length=50, description="File type (pdf, txt, docx, md)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentUpdate(BaseModel):
    """Request model for updating document metadata."""
    filename: Optional[str] = Field(None, max_length=255, description="New filename")
    status: Optional[str] = Field(None, description="Document status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Response model for document."""
    id: str
    user_id: str
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    uploaded_at: str
    processed_at: Optional[str] = None
    chunk_count: int = 0
    status: str = "uploaded"
    metadata: Dict[str, Any] = {}


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentPreviewResponse(BaseModel):
    """Response model for document preview."""
    content: str


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List documents for the current user.
    
    Returns paginated list of document metadata for the authenticated user.
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
        
        # Build query
        query = supabase._client.table("documents").select("*", count="exact").eq("user_id", user_id)
        
        # Apply status filter if provided
        if status_filter:
            query = query.eq("status", status_filter)
        
        # Apply pagination
        from_index = (page - 1) * page_size
        to_index = from_index + page_size - 1
        
        result = query.range(from_index, to_index).execute()
        
        documents = []
        for doc in result.data:
            documents.append({
                "id": doc["id"],
                "user_id": doc["user_id"],
                "filename": doc["filename"],
                "file_path": doc.get("file_path"),
                "file_size": doc.get("file_size"),
                "file_type": doc.get("file_type"),
                "uploaded_at": doc["uploaded_at"],
                "processed_at": doc.get("processed_at"),
                "chunk_count": doc.get("chunk_count", 0),
                "status": doc.get("status", "uploaded"),
                "metadata": doc.get("metadata", {}),
            })
        
        total = result.count or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return {
            "documents": documents,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create document metadata.
    
    Creates metadata record for a document (without actual file upload).
    File upload will be handled separately in Task 3.1.
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
        
        # Prepare data for insertion
        doc_data = {
            "user_id": user_id,
            "filename": document_data.filename,
            "file_path": document_data.file_path,
            "file_size": document_data.file_size,
            "file_type": document_data.file_type,
            "status": "uploaded",
            "metadata": document_data.metadata or {},
        }
        
        # Insert into database
        result = supabase._client.table("documents").insert(doc_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document",
            )
        
        created_doc = result.data[0]
        
        return {
            "id": created_doc["id"],
            "user_id": created_doc["user_id"],
            "filename": created_doc["filename"],
            "file_path": created_doc.get("file_path"),
            "file_size": created_doc.get("file_size"),
            "file_type": created_doc.get("file_type"),
            "uploaded_at": created_doc["uploaded_at"],
            "processed_at": created_doc.get("processed_at"),
            "chunk_count": created_doc.get("chunk_count", 0),
            "status": created_doc.get("status", "uploaded"),
            "metadata": created_doc.get("metadata", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document",
        )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Upload a document file.
    
    Handles file upload with validation, stores in Supabase Storage,
    and creates document metadata record.
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
        
        # Validate file size
        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB",
            )
        
        # Validate file type
        filename = file.filename
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}",
            )
        
        # Generate unique file path
        file_id = str(uuid.uuid4())
        storage_path = f"documents/{user_id}/{file_id}.{file_ext}"
        
        # Upload to Supabase Storage
        try:
            # Use the storage bucket "documents" (should be created in Supabase)
            await supabase.upload_file(
                bucket="documents",
                path=storage_path,
                file_content=file_content,
                file_type=file.content_type or "application/octet-stream",
            )
        except Exception as e:
            logger.error(f"Failed to upload file to Supabase Storage: {e}")
            # Check if error indicates bucket not found
            error_str = str(e)
            if "Bucket not found" in error_str or "bucket not found" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Storage bucket 'documents' does not exist. Please create the bucket in Supabase Storage or contact administrator.",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage",
            )
        
        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                import json
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata JSON: {metadata}")
                metadata_dict = {"raw_metadata": metadata}
        
        # Create document metadata record
        doc_data = {
            "user_id": user_id,
            "filename": filename,
            "file_path": storage_path,
            "file_size": file_size,
            "file_type": file_ext,
            "status": "uploaded",
            "metadata": metadata_dict,
        }
        
        result = supabase._client.table("documents").insert(doc_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document metadata",
            )
        
        created_doc = result.data[0]
        
        # Add background task to process the document
        background_tasks.add_task(
            process_document_background,
            document_id=created_doc["id"],
            file_content=file_content,
            file_type=file_ext,
            filename=filename,
            user_id=user_id
        )
        
        return {
            "id": created_doc["id"],
            "user_id": created_doc["user_id"],
            "filename": created_doc["filename"],
            "file_path": created_doc.get("file_path"),
            "file_size": created_doc.get("file_size"),
            "file_type": created_doc.get("file_type"),
            "uploaded_at": created_doc["uploaded_at"],
            "processed_at": created_doc.get("processed_at"),
            "chunk_count": created_doc.get("chunk_count", 0),
            "status": created_doc.get("status", "uploaded"),
            "metadata": created_doc.get("metadata", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a specific document by ID.
    
    Returns document metadata for the authenticated user.
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
        
        # Fetch document
        result = supabase._client.table("documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        doc = result.data[0]
        
        return {
            "id": doc["id"],
            "user_id": doc["user_id"],
            "filename": doc["filename"],
            "file_path": doc.get("file_path"),
            "file_size": doc.get("file_size"),
            "file_type": doc.get("file_type"),
            "uploaded_at": doc["uploaded_at"],
            "processed_at": doc.get("processed_at"),
            "chunk_count": doc.get("chunk_count", 0),
            "status": doc.get("status", "uploaded"),
            "metadata": doc.get("metadata", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document",
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update document metadata.
    
    Updates document metadata (filename, status, metadata).
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
        
        # Check if document exists and belongs to user
        existing = supabase._client.table("documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        # Prepare update data
        update_data = {}
        if document_update.filename is not None:
            update_data["filename"] = document_update.filename
        
        if document_update.status is not None:
            valid_statuses = ["uploaded", "processing", "processed", "failed"]
            if document_update.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                )
            update_data["status"] = document_update.status
        
        if document_update.metadata is not None:
            # Merge with existing metadata
            existing_metadata = existing.data[0].get("metadata", {})
            merged_metadata = {**existing_metadata, **document_update.metadata}
            update_data["metadata"] = merged_metadata
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )
        
        # Update the document
        result = supabase._client.table("documents").update(update_data).eq("id", document_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document",
            )
        
        updated_doc = result.data[0]
        
        return {
            "id": updated_doc["id"],
            "user_id": updated_doc["user_id"],
            "filename": updated_doc["filename"],
            "file_path": updated_doc.get("file_path"),
            "file_size": updated_doc.get("file_size"),
            "file_type": updated_doc.get("file_type"),
            "uploaded_at": updated_doc["uploaded_at"],
            "processed_at": updated_doc.get("processed_at"),
            "chunk_count": updated_doc.get("chunk_count", 0),
            "status": updated_doc.get("status", "uploaded"),
            "metadata": updated_doc.get("metadata", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """
    Delete a document.
    
    Permanently deletes document metadata for the authenticated user.
    Note: This does not delete the actual file from storage (handled in Task 3.1).
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
        
        # Check if document exists and belongs to user
        existing = supabase._client.table("documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        doc = existing.data[0]
        file_path = doc.get("file_path")
        
        # Delete file from Supabase Storage if path exists
        if file_path:
            try:
                await supabase.delete_file(bucket="documents", path=file_path)
            except Exception as e:
                error_str = str(e)
                if "Bucket not found" in error_str or "bucket not found" in error_str:
                    logger.warning(f"Storage bucket 'documents' does not exist, skipping file deletion: {e}")
                else:
                    logger.warning(f"Failed to delete file from storage: {e}")
                # Continue with metadata deletion even if storage deletion fails
        
        # Delete the document (cascade will delete related chunks)
        supabase._client.table("documents").delete().eq("id", document_id).eq("user_id", user_id).execute()
        
        # Return 204 No Content
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.get("/{document_id}/preview", response_model=DocumentPreviewResponse)
async def get_document_preview(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a preview of document content.
    
    Returns the first 2000 characters of the document content,
    either from stored chunks or from the original file.
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
        
        # Check if document exists and belongs to user
        doc_exists = supabase._client.table("documents").select("id, status, file_path, file_type").eq("id", document_id).eq("user_id", user_id).execute()
        if not doc_exists.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        doc = doc_exists.data[0]
        status = doc.get("status", "uploaded")
        file_path = doc.get("file_path")
        file_type = doc.get("file_type")
        
        preview_content = ""
        
        # If document is processed, fetch chunks
        if status == "processed":
            # Fetch first few chunks (limit 5)
            result = supabase._client.table("document_chunks").select("content").eq("document_id", document_id).order("chunk_index").limit(5).execute()
            chunks = result.data or []
            for chunk in chunks:
                if chunk.get("content"):
                    preview_content += chunk["content"] + "\n\n"
            
            if not preview_content:
                preview_content = "Document processed but no content available."
                
        elif status == "processing":
            preview_content = "Document is currently being processed. Please check back in a few moments."
        elif status == "failed":
            preview_content = "Document processing failed. Please try uploading again or contact support."
        else:
            # Document uploaded but not yet processing
            preview_content = "Document has been uploaded and is queued for processing. Preview will be available shortly."
        
        # Limit preview length
        max_length = 2000
        if len(preview_content) > max_length:
            preview_content = preview_content[:max_length] + "..."
        
        return {"content": preview_content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document preview",
        )


@router.get("/{document_id}/chunks", response_model=List[Dict[str, Any]])
async def get_document_chunks(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get chunks for a specific document.
    
    Returns chunk metadata for a document (actual content may be in ChromaDB).
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
        
        # Check if document exists and belongs to user
        doc_exists = supabase._client.table("documents").select("id").eq("id", document_id).eq("user_id", user_id).execute()
        if not doc_exists.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        # Fetch chunks
        result = supabase._client.table("document_chunks").select("*").eq("document_id", document_id).order("chunk_index").execute()
        
        chunks = []
        for chunk in result.data:
            chunks.append({
                "id": chunk["id"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk.get("content"),
                "embedding_id": chunk.get("embedding_id"),
                "created_at": chunk["created_at"],
                "metadata": chunk.get("metadata", {}),
            })
        
        return chunks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document chunks",
        )


async def process_document_background(
    document_id: str,
    file_content: bytes,
    file_type: str,
    filename: str,
    user_id: str
) -> None:
    """
    Background task to process a document after upload.
    
    This function is called asynchronously to parse, clean, chunk,
    and store document content without blocking the upload response.
    """
    print(f"🔥 BACKGROUND TASK STARTED: {document_id}")
    try:
        logger.info(f"Starting background processing for document {document_id}")
        print("🔥 Initializing Supabase...")
        # Initialize Supabase client
        supabase = SupabaseClient()
        if not supabase._client:
            logger.error(f"Supabase client not initialized for document {document_id}")
            return
        print(f"🔥 Supabase client: {supabase._client is not None}")
        
        print("🔥 Updating status to processing...")
        # Update document status to processing
        try:
            supabase._client.table("documents").update({
                "status": "processing",
                "processed_at": None
            }).eq("id", document_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update document status to processing: {e}")
        print("🔥 Starting DocumentProcessor...")
        # Process the document
        processor = DocumentProcessor()
        await processor.process_document(
            document_id=document_id,
            file_content=file_content,
            file_type=file_type,
            filename=filename,
            user_id=user_id,
            supabase_client=supabase
        )
        
        logger.info(f"Background processing completed for document {document_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {traceback.format_exc()}")
        print(f"🔥 CRASHED: {traceback.format_exc()}")
        # Update document status to failed
        try:
            supabase = SupabaseClient()
            if supabase._client:
                supabase._client.table("documents").update({
                    "status": "failed",
                    "metadata": {
                        "error": str(e),
                        "processing_error": True
                    }
                }).eq("id", document_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update document status to failed: {update_error}")