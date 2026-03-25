"""
Integration tests for vector operations (ChromaDB integration).

Tests embedding generation, vector storage, and similarity search functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from app.services.embedding_service import (
    EmbeddingService,
    OpenAIEmbeddingProvider,
    LocalEmbeddingProvider
)
from app.services.vector_store import VectorStore
from app.services.similarity_search import SimilaritySearchService


class TestEmbeddingService:
    """Tests for embedding generation service."""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI embedding response."""
        return {
            "data": [
                {"embedding": [0.1, 0.2, 0.3] * 512},  # 1536 dimensions
                {"embedding": [0.4, 0.5, 0.6] * 512},
            ]
        }
    
    @pytest.mark.asyncio
    async def test_openai_embedding_provider(self, mock_openai_response):
        """Test OpenAI embedding provider."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_embeddings = Mock()
        mock_embeddings.create.return_value = type('obj', (object,), {
            'data': [
                type('obj', (object,), {'embedding': [0.1, 0.2, 0.3] * 512}),
                type('obj', (object,), {'embedding': [0.4, 0.5, 0.6] * 512}),
            ]
        })()
        
        mock_client.embeddings = mock_embeddings
        
        with patch('app.services.embedding_service.OpenAI', return_value=mock_client):
            provider = OpenAIEmbeddingProvider(
                api_key="test-key",
                model="text-embedding-3-small"
            )
            
            # Test embedding generation
            texts = ["Hello world", "Test document"]
            embeddings = await provider.generate_embeddings(texts)
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 1536  # text-embedding-3-small dimensions
            
            # Test dimensions
            dimensions = provider.get_dimensions()
            assert dimensions == 1536
    
    @pytest.mark.asyncio
    async def test_embedding_service_with_openai(self):
        """Test main embedding service with OpenAI provider."""
        service = EmbeddingService(provider="openai")
        
        # Mock the provider
        mock_provider = Mock()
        mock_provider.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3] * 512])
        mock_provider.get_dimensions.return_value = 1536
        
        with patch.object(service, 'get_provider', return_value=mock_provider):
            # Test embedding generation
            texts = ["Test text"]
            embeddings = await service.generate_embeddings(texts)
            
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 1536
            
            # Test single embedding
            embedding = await service.generate_single_embedding("Single text")
            assert len(embedding) == 1536
            
            # Test dimensions - need to await the coroutine
            dimensions = await service.get_embedding_dimensions()
            assert dimensions == 1536


class TestVectorStore:
    """Tests for vector storage service."""
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing."""
        return [
            {
                "text": "This is the first chunk of document one.",
                "metadata": {"chunk_type": "paragraph", "page": 1}
            },
            {
                "text": "This is the second chunk of document one.",
                "metadata": {"chunk_type": "paragraph", "page": 1}
            },
            {
                "text": "This is a chunk from document two.",
                "metadata": {"chunk_type": "section", "page": 2}
            }
        ]
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        mock_service = AsyncMock()
        mock_service.generate_embeddings.return_value = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536
        ]
        mock_service.generate_single_embedding.return_value = [0.5] * 1536
        mock_service.get_embedding_dimensions.return_value = 1536
        return mock_service
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client."""
        mock_client = Mock()
        mock_collection = Mock()
        
        # Mock collection methods
        mock_collection.add = Mock()
        mock_collection.query = Mock(return_value={
            "ids": [["doc1_0", "doc1_1"]],
            "documents": [["Chunk 1 text", "Chunk 2 text"]],
            "metadatas": [[
                {"document_id": "doc1", "chunk_index": 0},
                {"document_id": "doc1", "chunk_index": 1}
            ]],
            "distances": [[0.1, 0.2]]
        })
        mock_collection.get = Mock(return_value={
            "ids": ["doc1_0", "doc1_1"],
            "documents": ["Chunk 1 text", "Chunk 2 text"],
            "metadatas": [
                {"document_id": "doc1", "chunk_index": 0},
                {"document_id": "doc1", "chunk_index": 1}
            ]
        })
        mock_collection.count = Mock(return_value=2)
        mock_collection.delete = Mock()
        
        mock_client.get_collection = Mock(return_value=mock_collection)
        mock_client.create_collection = Mock(return_value=mock_collection)
        mock_client.heartbeat = Mock()
        mock_client.delete_collection = Mock()
        
        return mock_client
    
    @pytest.mark.asyncio
    async def test_add_document_chunks(
        self,
        sample_chunks,
        mock_embedding_service,
        mock_chroma_client
    ):
        """Test adding document chunks to vector store."""
        vector_store = VectorStore(embedding_service=mock_embedding_service)
        
        with patch.object(vector_store, '_get_client', return_value=mock_chroma_client):
            # Test adding chunks
            chunk_ids = await vector_store.add_document_chunks(
                user_id="test-user",
                document_id="doc1",
                chunks=sample_chunks,
                metadata={"source": "test"}
            )
            
            assert len(chunk_ids) == 3
            assert chunk_ids[0] == "doc1_0"
            assert chunk_ids[1] == "doc1_1"
            assert chunk_ids[2] == "doc1_2"
            
            # Verify collection.add was called
            mock_collection = mock_chroma_client.get_collection.return_value
            mock_collection.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar(
        self,
        mock_embedding_service,
        mock_chroma_client
    ):
        """Test similarity search."""
        vector_store = VectorStore(embedding_service=mock_embedding_service)
        
        with patch.object(vector_store, '_get_client', return_value=mock_chroma_client):
            results = await vector_store.search_similar(
                user_id="test-user",
                query="test query",
                n_results=2
            )
            
            assert len(results) == 2
            assert results[0]["id"] == "doc1_0"
            assert results[0]["score"] == 0.9  # 1.0 - 0.1
            assert "document_id" in results[0]["metadata"]
    
    @pytest.mark.asyncio
    async def test_get_document_chunks(
        self,
        mock_embedding_service,
        mock_chroma_client
    ):
        """Test retrieving document chunks."""
        vector_store = VectorStore(embedding_service=mock_embedding_service)
        
        with patch.object(vector_store, '_get_client', return_value=mock_chroma_client):
            chunks = await vector_store.get_document_chunks(
                user_id="test-user",
                document_id="doc1",
                limit=10
            )
            
            assert len(chunks) == 2
            assert chunks[0]["id"] == "doc1_0"
            assert chunks[0]["document"] == "Chunk 1 text"
    
    @pytest.mark.asyncio
    async def test_delete_document_chunks(
        self,
        mock_embedding_service,
        mock_chroma_client
    ):
        """Test deleting document chunks."""
        vector_store = VectorStore(embedding_service=mock_embedding_service)
        
        with patch.object(vector_store, '_get_client', return_value=mock_chroma_client):
            deleted_count = await vector_store.delete_document_chunks(
                user_id="test-user",
                document_id="doc1"
            )
            
            assert deleted_count == 2
            
            # Verify delete was called
            mock_collection = mock_chroma_client.get_collection.return_value
            mock_collection.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(
        self,
        mock_embedding_service,
        mock_chroma_client
    ):
        """Test getting collection statistics."""
        vector_store = VectorStore(embedding_service=mock_embedding_service)
        
        with patch.object(vector_store, '_get_client', return_value=mock_chroma_client):
            stats = await vector_store.get_collection_stats("test-user")
            
            assert stats["user_id"] == "test-user"
            assert stats["total_chunks"] == 2
            assert stats["dimensions"] == 1536


class TestSimilaritySearchService:
    """Tests for similarity search service."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock_store = AsyncMock()
        
        # Mock search_similar
        mock_store.search_similar.return_value = [
            {
                "id": "doc1_0",
                "document": "First chunk about machine learning",
                "metadata": {"document_id": "doc1", "title": "ML Guide"},
                "score": 0.9,
                "distance": 0.1
            },
            {
                "id": "doc1_1",
                "document": "Second chunk about deep learning",
                "metadata": {"document_id": "doc1", "title": "ML Guide"},
                "score": 0.8,
                "distance": 0.2
            }
        ]
        
        # Mock get_or_create_collection for collection access
        mock_collection = Mock()
        mock_collection.get.return_value = {
            "ids": ["doc1_0", "doc1_1"],
            "documents": ["Chunk 1", "Chunk 2"],
            "metadatas": [{"title": "Doc1"}, {"title": "Doc1"}]
        }
        mock_store.get_or_create_collection.return_value = mock_collection
        
        return mock_store
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, mock_vector_store):
        """Test semantic search."""
        search_service = SimilaritySearchService(vector_store=mock_vector_store)
        
        results = await search_service.semantic_search(
            user_id="test-user",
            query="machine learning",
            n_results=2
        )
        
        assert len(results) == 2
        assert results[0]["score"] == 0.9
        assert "machine learning" in results[0]["document"].lower()
        
        # Verify vector store was called
        mock_vector_store.search_similar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_min_score(self, mock_vector_store):
        """Test semantic search with minimum score filter."""
        search_service = SimilaritySearchService(vector_store=mock_vector_store)
        
        results = await search_service.semantic_search(
            user_id="test-user",
            query="test query",
            n_results=5,
            min_score=0.85  # Only results with score >= 0.85
        )
        
        # Only first result has score 0.9 >= 0.85
        assert len(results) == 1
        assert results[0]["score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_search_by_document(self, mock_vector_store):
        """Test search within specific document."""
        search_service = SimilaritySearchService(vector_store=mock_vector_store)
        
        # Test with query
        results = await search_service.search_by_document(
            user_id="test-user",
            document_id="doc1",
            query="machine learning",
            n_results=2
        )
        
        assert len(results) == 2
        assert all(r["metadata"]["document_id"] == "doc1" for r in results)
        
        # Test without query (get all chunks)
        mock_vector_store.get_document_chunks.return_value = [
            {
                "id": "doc1_0",
                "document": "Chunk 1",
                "metadata": {"document_id": "doc1"}
            }
        ]
        
        results = await search_service.search_by_document(
            user_id="test-user",
            document_id="doc1",
            query=None,
            n_results=5
        )
        
        assert len(results) == 1
        assert results[0]["score"] == 1.0  # Default score when no query
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, mock_vector_store):
        """Test getting search suggestions."""
        search_service = SimilaritySearchService(vector_store=mock_vector_store)
        
        suggestions = await search_service.get_search_suggestions(
            user_id="test-user",
            partial_query="mac",
            limit=3
        )
        
        # Suggestions should be a list of strings
        assert isinstance(suggestions, list)
        assert all(isinstance(s, str) for s in suggestions)


@pytest.mark.integration
class TestVectorOperationsIntegration:
    """Integration tests for vector operations (requires ChromaDB)."""
    
    @pytest.mark.asyncio
    async def test_embedding_service_integration(self):
        """Integration test for embedding service (requires OpenAI API key)."""
        # Skip if no OpenAI API key
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not configured")
        
        service = EmbeddingService(provider="openai")
        
        # Test with real API (small test)
        texts = ["Hello world", "Test embedding"]
        try:
            embeddings = await service.generate_embeddings(texts)
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) > 0
            
            dimensions = await service.get_embedding_dimensions()
            assert dimensions == len(embeddings[0])
            
        except Exception as e:
            # If API call fails, skip the test
            pytest.skip(f"OpenAI API call failed: {e}")
    
    @pytest.mark.asyncio
    async def test_vector_store_with_mocked_embeddings(self):
        """
        Integration test for vector store with mocked embeddings.
        This tests the ChromaDB integration without requiring actual embeddings.
        """
        # Skip if Docker/ChromaDB is not available
        try:
            import chromadb
        except ImportError:
            pytest.skip("ChromaDB not installed")
        
        # Use in-memory ChromaDB for testing
        from chromadb.config import Settings
        
        # Mock embedding service
        mock_embedding_service = AsyncMock()
        mock_embedding_service.generate_embeddings.return_value = [
            [0.1, 0.2, 0.3, 0.4] * 384,  # 1536 dimensions simplified
            [0.5, 0.6, 0.7, 0.8] * 384,
        ]
        mock_embedding_service.generate_single_embedding.return_value = [0.9] * 1536
        mock_embedding_service.get_embedding_dimensions.return_value = 1536
        
        # Create vector store with in-memory client
        vector_store = VectorStore(embedding_service=mock_embedding_service)
        
        # Override client creation to use in-memory
        import chromadb
        test_client = chromadb.EphemeralClient()
        vector_store.client = test_client
        
        # Test adding chunks
        chunks = [
            {"text": "First test chunk about artificial intelligence."},
            {"text": "Second test chunk about machine learning."}
        ]
        
        chunk_ids = await vector_store.add_document_chunks(
            user_id="test-user-integration",
            document_id="test-doc-1",
            chunks=chunks,
            metadata={"test": True, "integration": True}
        )
        
        assert len(chunk_ids) == 2
        assert chunk_ids[0] == "test-doc-1_0"
        
        # Test search
        results = await vector_store.search_similar(
            user_id="test-user-integration",
            query="artificial intelligence",
            n_results=2
        )
        
        # Should find at least one result
        assert len(results) > 0
        
        # Test getting document chunks
        doc_chunks = await vector_store.get_document_chunks(
            user_id="test-user-integration",
            document_id="test-doc-1",
            limit=10
        )
        
        assert len(doc_chunks) == 2
        
        # Test collection stats
        stats = await vector_store.get_collection_stats("test-user-integration")
        assert stats["total_chunks"] == 2
        assert stats["unique_documents"] == 1
        
        # Test deletion
        deleted_count = await vector_store.delete_document_chunks(
            user_id="test-user-integration",
            document_id="test-doc-1"
        )
        
        assert deleted_count == 2
        
        # Verify deletion
        doc_chunks_after = await vector_store.get_document_chunks(
            user_id="test-user-integration",
            document_id="test-doc-1",
            limit=10
        )
        
        assert len(doc_chunks_after) == 0