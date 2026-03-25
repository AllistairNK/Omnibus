"""
Advanced similarity search service with support for hybrid search, re-ranking,
and result filtering.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SimilaritySearchService:
    """Advanced similarity search service."""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize similarity search service.
        
        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
        """
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService()
    
    async def semantic_search(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            user_id: User ID
            query: Search query
            n_results: Number of results to return
            filter_conditions: Metadata filters
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of search results filtered by min_score
        """
        # Get raw search results
        results = await self.vector_store.search_similar(
            user_id=user_id,
            query=query,
            n_results=n_results * 2,  # Get more results for filtering
            filter_conditions=filter_conditions
        )
        
        # Filter by minimum score
        filtered_results = [
            result for result in results 
            if result.get("score", 0) >= min_score
        ]
        
        # Limit to requested number of results
        return filtered_results[:n_results]
    
    async def hybrid_search(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword matching.
        
        Args:
            user_id: User ID
            query: Search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            
        Returns:
            List of hybrid search results
        """
        # Get semantic search results
        semantic_results = await self.semantic_search(
            user_id=user_id,
            query=query,
            n_results=n_results * 2
        )
        
        # Simple keyword matching (in production, use proper keyword search)
        keyword_results = await self._keyword_search(
            user_id=user_id,
            query=query,
            n_results=n_results * 2
        )
        
        # Combine results
        combined_results = self._combine_results(
            semantic_results, keyword_results,
            semantic_weight, keyword_weight
        )
        
        return combined_results[:n_results]
    
    async def _keyword_search(
        self,
        user_id: str,
        query: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Simple keyword search implementation.
        
        Note: In production, this would use a proper keyword search engine
        like Elasticsearch or PostgreSQL full-text search.
        """
        # Get all documents from vector store
        collection = await self.vector_store.get_or_create_collection(user_id)
        all_docs = collection.get(limit=1000, include=["documents", "metadatas"])
        
        # Simple keyword matching
        query_keywords = set(query.lower().split())
        scored_results = []
        
        for i in range(len(all_docs["ids"])):
            document = all_docs["documents"][i].lower()
            metadata = all_docs["metadatas"][i]
            
            # Count keyword matches
            matches = sum(1 for keyword in query_keywords if keyword in document)
            
            if matches > 0:
                # Simple scoring based on match count and document length
                score = matches / len(query_keywords)
                
                scored_results.append({
                    "id": all_docs["ids"][i],
                    "document": all_docs["documents"][i],
                    "metadata": metadata,
                    "score": score,
                    "distance": 1.0 - score,  # Convert to distance-like metric
                    "search_type": "keyword"
                })
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:n_results]
    
    def _combine_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword search results."""
        # Create a map of result ID to result
        all_results = {}
        
        # Add semantic results with weighted scores
        for result in semantic_results:
            result_id = result["id"]
            all_results[result_id] = {
                **result,
                "semantic_score": result.get("score", 0),
                "keyword_score": 0,
                "combined_score": result.get("score", 0) * semantic_weight
            }
        
        # Add keyword results with weighted scores
        for result in keyword_results:
            result_id = result["id"]
            keyword_score = result.get("score", 0)
            
            if result_id in all_results:
                # Update existing result
                all_results[result_id]["keyword_score"] = keyword_score
                all_results[result_id]["combined_score"] += keyword_score * keyword_weight
            else:
                # Add new result
                all_results[result_id] = {
                    **result,
                    "semantic_score": 0,
                    "keyword_score": keyword_score,
                    "combined_score": keyword_score * keyword_weight
                }
        
        # Convert to list and sort by combined score
        combined_list = list(all_results.values())
        combined_list.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return combined_list
    
    async def search_with_reranking(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        reranker_model: str = "cross-encoder"
    ) -> List[Dict[str, Any]]:
        """
        Perform search with re-ranking for improved relevance.
        
        Args:
            user_id: User ID
            query: Search query
            n_results: Number of final results
            reranker_model: Re-ranker model to use
            
        Returns:
            Re-ranked search results
        """
        # Get initial results (more than needed for re-ranking)
        initial_results = await self.semantic_search(
            user_id=user_id,
            query=query,
            n_results=n_results * 3
        )
        
        if not initial_results:
            return []
        
        # Apply re-ranking
        reranked_results = await self._rerank_results(
            query=query,
            results=initial_results,
            model=reranker_model
        )
        
        return reranked_results[:n_results]
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        model: str = "cross-encoder"
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results using a re-ranker model.
        
        Note: This is a placeholder implementation. In production,
        you would use a proper re-ranker like sentence-transformers cross-encoder.
        """
        # Placeholder implementation - returns results as-is
        # In production, you would:
        # 1. Load a cross-encoder model
        # 2. Compute relevance scores for each (query, document) pair
        # 3. Re-sort results based on relevance scores
        
        logger.info(f"Using placeholder re-ranker (model: {model})")
        
        # Simple heuristic: boost results with query terms in title/metadata
        query_terms = set(query.lower().split())
        
        for result in results:
            metadata = result.get("metadata", {})
            document_text = result.get("document", "").lower()
            
            # Count matches in metadata fields
            metadata_matches = 0
            for field in ["title", "filename", "subject"]:
                if field in metadata:
                    field_value = str(metadata[field]).lower()
                    metadata_matches += sum(
                        1 for term in query_terms if term in field_value
                    )
            
            # Count matches in document
            document_matches = sum(
                1 for term in query_terms if term in document_text
            )
            
            # Apply boost
            boost = 1.0 + (metadata_matches * 0.1) + (document_matches * 0.05)
            result["reranked_score"] = result.get("score", 0) * boost
        
        # Sort by reranked score
        results.sort(key=lambda x: x.get("reranked_score", 0), reverse=True)
        return results
    
    async def search_by_document(
        self,
        user_id: str,
        document_id: str,
        query: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search within a specific document.
        
        Args:
            user_id: User ID
            document_id: Document ID to search within
            query: Optional query (if None, returns all chunks)
            n_results: Number of results to return
            
        Returns:
            Search results from the specified document
        """
        if query:
            # Search with filter for document_id
            results = await self.vector_store.search_similar(
                user_id=user_id,
                query=query,
                n_results=n_results,
                filter_conditions={"document_id": document_id}
            )
        else:
            # Get all chunks for the document
            chunks = await self.vector_store.get_document_chunks(
                user_id=user_id,
                document_id=document_id,
                limit=n_results
            )
            
            # Convert to search result format
            results = []
            for chunk in chunks:
                results.append({
                    "id": chunk["id"],
                    "document": chunk["document"],
                    "metadata": chunk["metadata"],
                    "score": 1.0,  # No relevance scoring when no query
                    "distance": 0.0
                })
        
        return results
    
    async def get_search_suggestions(
        self,
        user_id: str,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on partial query.
        
        Args:
            user_id: User ID
            partial_query: Partial query string
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested search queries
        """
        # Get collection
        collection = await self.vector_store.get_or_create_collection(user_id)
        
        # Get sample documents
        sample_docs = collection.get(limit=100, include=["documents"])
        
        # Extract potential suggestions (simple implementation)
        suggestions = set()
        partial_lower = partial_query.lower()
        
        for doc in sample_docs["documents"]:
            # Extract words from document
            words = doc.lower().split()
            
            # Find words that start with the partial query
            for word in words:
                if word.startswith(partial_lower) and len(word) > len(partial_lower):
                    suggestions.add(word)
                    if len(suggestions) >= limit * 2:
                        break
            
            if len(suggestions) >= limit * 2:
                break
        
        # Convert to list and sort
        suggestions_list = list(suggestions)
        suggestions_list.sort()
        
        return suggestions_list[:limit]


# Global instance for easy access
similarity_search = SimilaritySearchService()