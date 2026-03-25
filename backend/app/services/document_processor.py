"""
Main document processing service that orchestrates parsing, cleaning, and chunking.

This service provides a high-level interface for processing documents
and tracking chunk metadata in the database.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.core.supabase import SupabaseClient
from app.services.document_parser import DocumentParser
from app.services.text_cleaner import TextCleaner
from app.services.document_chunker import DocumentChunker

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates document processing pipeline."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunk_strategy: str = "hybrid"
    ):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            chunk_strategy: Chunking strategy ("fixed", "paragraph", "sentence", "hybrid")
        """
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=chunk_strategy
        )
    
    async def process_document(
        self,
        document_id: str,
        file_content: bytes,
        file_type: str,
        filename: str,
        user_id: str,
        supabase_client: Optional[SupabaseClient] = None
    ) -> Dict[str, any]:
        """
        Process a document: parse, clean, chunk, and store metadata.
        
        Args:
            document_id: ID of the document in database
            file_content: Raw file bytes
            file_type: File extension (pdf, docx, txt, md)
            filename: Original filename
            user_id: User ID who owns the document
            supabase_client: Optional Supabase client instance
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing document {document_id} ({filename})")
        
        try:
            # Step 1: Parse document
            parsed_text, parse_metadata = DocumentParser.parse_document(
                file_content, file_type, filename
            )
            
            # Step 2: Clean text
            cleaned_text = TextCleaner.clean_text(parsed_text, preserve_structure=True)
            text_metrics = TextCleaner.calculate_text_metrics(cleaned_text)
            
            # Step 3: Chunk text
            chunks = self.chunker.chunk_text(cleaned_text, parse_metadata)
            chunk_metrics = DocumentChunker.calculate_chunking_metrics(chunks)
            
            # Step 4: Store chunks in database if Supabase client provided
            chunk_records = []
            if supabase_client and supabase_client._client:
                chunk_records = await self._store_chunks_in_db(
                    document_id=document_id,
                    chunks=chunks,
                    user_id=user_id,
                    supabase_client=supabase_client
                )
            
            # Step 5: Update document status
            if supabase_client and supabase_client._client:
                await self._update_document_status(
                    document_id=document_id,
                    chunk_count=len(chunks),
                    supabase_client=supabase_client
                )
            
            # Prepare processing results
            processing_result = {
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type,
                "processing_success": True,
                "text_metrics": text_metrics,
                "chunk_metrics": chunk_metrics,
                "total_chunks": len(chunks),
                "parse_metadata": parse_metadata,
                "chunks_stored": len(chunk_records) if chunk_records else 0,
                "processed_at": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Document {document_id} processed successfully: {len(chunks)} chunks")
            return processing_result
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            
            # Update document status to failed
            if supabase_client and supabase_client._client:
                try:
                    await self._mark_document_failed(
                        document_id=document_id,
                        error_message=str(e),
                        supabase_client=supabase_client
                    )
                except Exception as update_error:
                    logger.error(f"Failed to update document status: {update_error}")
            
            raise
    
    async def _store_chunks_in_db(
        self,
        document_id: str,
        chunks: List[Dict],
        user_id: str,
        supabase_client: SupabaseClient
    ) -> List[Dict]:
        """
        Store chunks in database with metadata.
        
        Args:
            document_id: ID of the parent document
            chunks: List of chunk dictionaries
            user_id: User ID who owns the document
            supabase_client: Supabase client instance
            
        Returns:
            List of created chunk records
        """
        if not supabase_client._client:
            raise ValueError("Supabase client not initialized")
        
        chunk_records = []
        
        for chunk in chunks:
            # Generate unique ID for chunk
            chunk_id = str(uuid.uuid4())
            
            # Prepare chunk data for database
            chunk_data = {
                "id": chunk_id,
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["text"],
                "start_position": chunk.get("start_pos", 0),
                "end_position": chunk.get("end_pos", 0),
                "size_chars": chunk["size_chars"],
                "size_words": chunk["size_words"],
                "chunk_type": chunk.get("chunk_type", "unknown"),
                "metadata": {
                    "chunk_metadata": chunk.get("metadata", {}),
                    "document_metadata": chunk.get("document_metadata", {}),
                    "processing_metadata": {
                        "chunk_strategy": self.chunker.strategy,
                        "chunk_size": self.chunker.chunk_size,
                        "chunk_overlap": self.chunker.chunk_overlap,
                    }
                }
            }
            
            try:
                # Insert chunk into database
                result = supabase_client._client.table("document_chunks").insert(chunk_data).execute()
                
                if result.data:
                    chunk_records.append(result.data[0])
                else:
                    logger.warning(f"Failed to insert chunk {chunk_id} for document {document_id}")
                    
            except Exception as e:
                logger.error(f"Error inserting chunk {chunk_id}: {e}")
                # Continue with other chunks even if one fails
        
        logger.info(f"Stored {len(chunk_records)} chunks for document {document_id}")
        return chunk_records
    
    async def _update_document_status(
        self,
        document_id: str,
        chunk_count: int,
        supabase_client: SupabaseClient
    ) -> bool:
        """
        Update document status to 'processed' and set chunk count.
        
        Args:
            document_id: ID of the document
            chunk_count: Number of chunks created
            supabase_client: Supabase client instance
            
        Returns:
            True if update successful
        """
        if not supabase_client._client:
            return False
        
        try:
            update_data = {
                "status": "processed",
                "processed_at": datetime.utcnow().isoformat(),
                "chunk_count": chunk_count,
            }
            
            result = supabase_client._client.table("documents").update(update_data).eq("id", document_id).execute()
            
            if result.data:
                logger.info(f"Updated document {document_id} status to 'processed'")
                return True
            else:
                logger.warning(f"Failed to update document {document_id} status")
                return False
                
        except Exception as e:
            logger.error(f"Error updating document status for {document_id}: {e}")
            return False
    
    async def _mark_document_failed(
        self,
        document_id: str,
        error_message: str,
        supabase_client: SupabaseClient
    ) -> bool:
        """
        Mark document as failed processing.
        
        Args:
            document_id: ID of the document
            error_message: Error description
            supabase_client: Supabase client instance
            
        Returns:
            True if update successful
        """
        if not supabase_client._client:
            return False
        
        try:
            update_data = {
                "status": "failed",
                "processed_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "processing_error": error_message[:500]  # Limit error message length
                }
            }
            
            result = supabase_client._client.table("documents").update(update_data).eq("id", document_id).execute()
            
            if result.data:
                logger.info(f"Marked document {document_id} as 'failed'")
                return True
            else:
                logger.warning(f"Failed to mark document {document_id} as 'failed'")
                return False
                
        except Exception as e:
            logger.error(f"Error marking document {document_id} as failed: {e}")
            return False
    
    @staticmethod
    async def get_document_chunks(
        document_id: str,
        user_id: str,
        supabase_client: SupabaseClient,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        Retrieve chunks for a document.
        
        Args:
            document_id: ID of the document
            user_id: User ID for authorization
            supabase_client: Supabase client instance
            limit: Maximum number of chunks to return
            offset: Offset for pagination
            
        Returns:
            Tuple of (chunks_list, total_count)
        """
        if not supabase_client._client:
            return [], 0
        
        try:
            # Query chunks with pagination
            query = (
                supabase_client._client.table("document_chunks")
                .select("*", count="exact")
                .eq("document_id", document_id)
                .eq("user_id", user_id)
                .order("chunk_index")
                .range(offset, offset + limit - 1)
            )
            
            result = query.execute()
            
            chunks = result.data or []
            total_count = result.count or 0
            
            return chunks, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving chunks for document {document_id}: {e}")
            return [], 0
    
    @staticmethod
    async def delete_document_chunks(
        document_id: str,
        user_id: str,
        supabase_client: SupabaseClient
    ) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: ID of the document
            user_id: User ID for authorization
            supabase_client: Supabase client instance
            
        Returns:
            True if deletion successful
        """
        if not supabase_client._client:
            return False
        
        try:
            # Delete chunks
            result = (
                supabase_client._client.table("document_chunks")
                .delete()
                .eq("document_id", document_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            logger.info(f"Deleted chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chunks for document {document_id}: {e}")
            return False