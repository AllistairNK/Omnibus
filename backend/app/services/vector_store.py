"""
Vector storage service for managing document embeddings in ChromaDB.

Provides functionality for storing, retrieving, and searching vector embeddings
with support for per-user collections.
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidDimensionException

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector storage service for ChromaDB operations."""
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize vector store.
        
        Args:
            embedding_service: Embedding service instance (creates new if None)
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.client = None
        self._dimensions = None
    
    async def _get_client(self):
        if self.client is not None:
            return self.client
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        def connect():
            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            client.heartbeat()
            return client
        
        try:
            self.client = await loop.run_in_executor(None, connect)
            logger.info(f"Connected to ChromaDB")
        except Exception as e:
            logger.warning(f"ChromaDB server failed: {e}, falling back to persistent")
            self.client = await loop.run_in_executor(
                None,
                lambda: chromadb.PersistentClient(path="./chroma_data")
            )
        
        return self.client  
    
    def _get_collection_name(self, user_id: str) -> str:
        """Generate collection name for a user."""
        return f"user_{user_id}_documents"
    
    async def _get_embedding_dimensions(self) -> int:
        """Get embedding dimensions from the embedding service."""
        if self._dimensions is None:
            self._dimensions = await self.embedding_service.get_embedding_dimensions()
        return self._dimensions
    
    async def get_or_create_collection(self, user_id: str) -> chromadb.Collection:
        """
        Get or create a collection for a user.
        
        Args:
            user_id: User ID for the collection
            
        Returns:
            ChromaDB collection instance
        """
        import asyncio
        loop = asyncio.get_running_loop()
        client = await self._get_client()
        collection_name = self._get_collection_name(user_id)
        
        def _get_or_create():
            try:
                return client.get_collection(name=collection_name)
            except Exception:
                return client.create_collection(
                    name=collection_name,
                    metadata={"user_id": user_id},
                    embedding_function=None
                )
        
        return await loop.run_in_executor(None, _get_or_create)
        try:
            # Try to get existing collection
            collection = client.get_collection(name=collection_name)
            logger.debug(f"Retrieved existing collection: {collection_name}")
        except Exception:
            # Create new collection
            dimensions = await self._get_embedding_dimensions()
            collection = client.create_collection(
                name=collection_name,
                metadata={"user_id": user_id, "created_at": datetime.now().isoformat()},
                embedding_function=None  # We'll compute embeddings ourselves
            )
            logger.info(f"Created new collection: {collection_name} with {dimensions} dimensions")
        
        return collection
    
    async def add_document_chunks(
        self,
        user_id: str,
        document_id: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Add document chunks to vector store.
        
        Args:
            user_id: User ID
            document_id: Document ID
            chunks: List of chunk dictionaries with "text" and optional "metadata"
            metadata: Additional metadata for all chunks
            
        Returns:
            List of chunk IDs added to vector store
        """
        if not chunks:
            return []
        print(f"🔥 VS: extracting texts")
        # Extract texts for embedding
        texts = [chunk.get("text", "") for chunk in chunks]
        print(f"🔥 VS: generating embeddings for {len(texts)} texts")
        # Generate embeddings
        embeddings = await self.embedding_service.generate_embeddings(texts)
        
        # Prepare metadata for each chunk
        chunk_metadatas = []
        chunk_ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "document_id": document_id,
                "chunk_index": i,
                "user_id": user_id,
                "chunk_size": len(chunk.get("text", "")),
                "created_at": datetime.now().isoformat(),
            }
            
            # Add chunk-specific metadata
            if "metadata" in chunk and isinstance(chunk["metadata"], dict):
                chunk_metadata.update(chunk["metadata"])
            
            # Add global metadata
            if metadata:
                chunk_metadata.update(metadata)
            
            chunk_metadatas.append(chunk_metadata)
            chunk_ids.append(f"{document_id}_{i}")
        print(f"🔥 VS: embeddings done, adding to ChromaDB")
        # Get collection and add documents
        collection = await self.get_or_create_collection(user_id)
        
        try:
            print(f"🔥 VS: got collection, calling collection.add")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            ))
            print(f"🔥 VS: done")
            logger.info(f"Added {len(chunks)} chunks for document {document_id} to vector store")
            
        except InvalidDimensionException as e:
            logger.error(f"Dimension mismatch error: {e}")
            # This could happen if collection was created with different dimensions
            # We need to recreate the collection with correct dimensions
            await self._recreate_collection_with_correct_dimensions(user_id, collection)
            
            # Try again with the new collection
            collection = await self.get_or_create_collection(user_id)
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
        print(f"🔥 VS: done")
        return chunk_ids
    
    async def _recreate_collection_with_correct_dimensions(
        self, 
        user_id: str, 
        old_collection: chromadb.Collection
    ):
        """Recreate collection with correct embedding dimensions."""
        client = await self._get_client()
        collection_name = self._get_collection_name(user_id)
        
        try:
            # Delete old collection
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection {collection_name} due to dimension mismatch")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")
        
        # Collection will be recreated on next get_or_create_collection call
    
    async def search_similar(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents/chunks.
        
        Args:
            user_id: User ID
            query: Search query text
            n_results: Number of results to return
            filter_conditions: Optional metadata filters
            
        Returns:
            List of search results with metadata
        """
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_single_embedding(query)
        
        # Get collection
        collection = await self.get_or_create_collection(user_id)
        
        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_conditions,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "score": 1.0 - results["distances"][0][i]  # Convert distance to similarity score
                })
        
        return formatted_results
    
    async def get_document_chunks(
        self,
        user_id: str,
        document_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.
        
        Args:
            user_id: User ID
            document_id: Document ID
            limit: Maximum number of chunks to return
            
        Returns:
            List of document chunks with metadata
        """
        collection = await self.get_or_create_collection(user_id)
        
        # Query with filter for document_id
        results = collection.get(
            where={"document_id": document_id},
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        formatted_chunks = []
        for i in range(len(results["ids"])):
            formatted_chunks.append({
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
        
        return formatted_chunks
    
    async def delete_document_chunks(
        self,
        user_id: str,
        document_id: str
    ) -> int:
        """
        Delete all chunks for a specific document.
        
        Args:
            user_id: User ID
            document_id: Document ID
            
        Returns:
            Number of chunks deleted
        """
        collection = await self.get_or_create_collection(user_id)
        
        # Get chunk IDs for this document
        results = collection.get(
            where={"document_id": document_id},
            include=[]
        )
        
        if not results["ids"]:
            return 0
        
        # Delete the chunks
        collection.delete(ids=results["ids"])
        logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        
        return len(results["ids"])
    
    async def get_collection_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for a user's collection.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with collection statistics
        """
        collection = await self.get_or_create_collection(user_id)
        
        # Get count of items in collection
        count = collection.count()
        
        # Get unique document IDs
        results = collection.get(include=["metadatas"])
        document_ids = set()
        for metadata in results["metadatas"]:
            if "document_id" in metadata:
                document_ids.add(metadata["document_id"])
        
        return {
            "user_id": user_id,
            "collection_name": self._get_collection_name(user_id),
            "total_chunks": count,
            "unique_documents": len(document_ids),
            "dimensions": await self._get_embedding_dimensions()
        }


# Global instance for easy access
vector_store = VectorStore()