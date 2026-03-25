"""
Integration tests for the full RAG pipeline.

Tests the complete RAG workflow from document ingestion to response generation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.similarity_search import SimilaritySearchService
from app.services.vector_store import VectorStore


class TestRAGPipeline:
    """Test suite for RAG pipeline integration."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        mock = AsyncMock(spec=LLMService)
        mock.is_available.return_value = True
        mock.chat_completion.return_value = {
            "content": "This is a test response based on the provided context.",
            "model": "gpt-5-nano",
            "tokens_used": 50,
            "finish_reason": "stop"
        }
        return mock
    
    @pytest.fixture
    def mock_similarity_search(self):
        """Mock similarity search service."""
        mock = AsyncMock(spec=SimilaritySearchService)
        mock.semantic_search.return_value = [
            {
                "content": "Test document content about AI and machine learning.",
                "metadata": {"source": "test_doc.pdf", "page": 1},
                "score": 0.85,
                "document_id": "doc_123",
                "chunk_index": 0,
                "source": "Test Document"
            },
            {
                "content": "Another relevant chunk about neural networks.",
                "metadata": {"source": "test_doc.pdf", "page": 2},
                "score": 0.72,
                "document_id": "doc_123",
                "chunk_index": 1,
                "source": "Test Document"
            }
        ]
        return mock
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock = AsyncMock(spec=VectorStore)
        return mock
    
    @pytest.fixture
    def rag_service(
        self,
        mock_llm_service,
        mock_similarity_search,
        mock_vector_store
    ):
        """Create RAG service with mocked dependencies."""
        return RAGService(
            llm_service=mock_llm_service,
            similarity_search_service=mock_similarity_search,
            vector_store=mock_vector_store
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_context(self, rag_service):
        """Test context retrieval from vector store."""
        # Arrange
        user_id = "test_user_123"
        query = "What is machine learning?"
        
        # Act
        context_docs = await rag_service.retrieve_context(
            user_id=user_id,
            query=query,
            n_results=3,
            min_score=0.5
        )
        
        # Assert
        assert isinstance(context_docs, list)
        assert len(context_docs) == 2  # From mock
        assert context_docs[0]["score"] == 0.85
        assert context_docs[0]["document_id"] == "doc_123"
        assert "content" in context_docs[0]
    
    @pytest.mark.asyncio
    async def test_format_context_for_prompt(self, rag_service):
        """Test context formatting for prompt."""
        # Arrange
        context_docs = [
            {
                "content": "First document chunk.",
                "metadata": {"source": "doc1.pdf"},
                "score": 0.9,
                "document_id": "doc1",
                "chunk_index": 0,
                "source": "Document 1"
            },
            {
                "content": "Second document chunk.",
                "metadata": {"source": "doc2.pdf"},
                "score": 0.8,
                "document_id": "doc2",
                "chunk_index": 1,
                "source": "Document 2"
            }
        ]
        
        # Act
        formatted_context = rag_service.format_context_for_prompt(
            context_docs=context_docs,
            max_tokens=1000
        )
        
        # Assert
        assert isinstance(formatted_context, str)
        assert "First document chunk" in formatted_context
        assert "Second document chunk" in formatted_context
        assert "Document 1" in formatted_context
        assert "0.90" in formatted_context  # Score formatted
    
    @pytest.mark.asyncio
    async def test_format_chat_history_for_prompt(self, rag_service):
        """Test chat history formatting."""
        # Arrange
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "What is AI?"}
        ]
        
        # Act
        formatted_history = rag_service.format_chat_history_for_prompt(
            chat_history=chat_history,
            max_messages=5
        )
        
        # Assert
        assert isinstance(formatted_history, str)
        assert "User: Hello" in formatted_history
        assert "Assistant: Hi there!" in formatted_history
        assert "User: What is AI?" in formatted_history
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_basic(self, rag_service):
        """Test basic RAG response generation."""
        # Arrange
        user_id = "test_user_123"
        query = "Explain machine learning"
        
        # Act
        response = await rag_service.generate_rag_response(
            user_id=user_id,
            query=query,
            chat_history=None,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500,
            include_sources=True
        )
        
        # Assert
        assert isinstance(response, dict)
        assert "content" in response
        assert "model" in response
        assert "tokens_used" in response
        assert "context_used" in response
        assert "context_document_count" in response
        assert "sources" in response
        assert response["context_used"] is True
        assert response["context_document_count"] == 2
        assert len(response["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_with_history(self, rag_service):
        """Test RAG response generation with chat history."""
        # Arrange
        user_id = "test_user_123"
        query = "Tell me more"
        chat_history = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI is artificial intelligence."}
        ]
        
        # Act
        response = await rag_service.generate_rag_response(
            user_id=user_id,
            query=query,
            chat_history=chat_history,
            include_sources=True
        )
        
        # Assert
        assert response["content"] is not None
        assert response["context_used"] is True
    
    @pytest.mark.asyncio
    async def test_generate_rag_response_no_context(self, rag_service):
        """Test RAG response when no context is found."""
        # Arrange
        user_id = "test_user_123"
        query = "Explain quantum physics"
        
        # Mock empty context
        rag_service.similarity_search_service.semantic_search.return_value = []
        
        # Act
        response = await rag_service.generate_rag_response(
            user_id=user_id,
            query=query,
            include_sources=True
        )
        
        # Assert
        assert response["content"] is not None
        assert response["context_used"] is False
        assert response["context_document_count"] == 0
        assert len(response["sources"]) == 0
    
    @pytest.mark.asyncio
    async def test_citation_formatting(self, rag_service):
        """Test citation formatting."""
        # Arrange
        sources = [
            {
                "document_id": "doc1",
                "chunk_index": 0,
                "source": "Research Paper 2024",
                "relevance_score": 0.9,
                "content_preview": "AI is transforming industries..."
            },
            {
                "document_id": "doc2",
                "chunk_index": 1,
                "source": "Technical Report",
                "relevance_score": 0.8,
                "content_preview": "Machine learning algorithms..."
            }
        ]
        
        # Test numeric citations
        citation_text, formatted_sources = rag_service._format_citations(
            sources=sources,
            citation_style="numeric"
        )
        
        # Assert
        assert "[1]" in citation_text
        assert "[2]" in citation_text
        assert len(formatted_sources) == 2
        assert formatted_sources[0]["citation_number"] == 1
        
        # Test inline citations
        citation_text, formatted_sources = rag_service._format_citations(
            sources=sources,
            citation_style="inline"
        )
        
        # Assert
        assert "Sources:" in citation_text
        assert "Research Paper 2024" in citation_text
    
    @pytest.mark.asyncio
    async def test_add_citations_to_response(self, rag_service):
        """Test adding citations to response text."""
        # Arrange
        response_text = "AI is transforming industries through automation."
        sources = [
            {
                "document_id": "doc1",
                "source": "Research Paper",
                "relevance_score": 0.9
            }
        ]
        
        # Act
        response_with_citations, formatted_sources = rag_service._add_citations_to_response(
            response_text=response_text,
            sources=sources,
            citation_style="numeric"
        )
        
        # Assert
        assert response_text in response_with_citations
        assert "References:" in response_with_citations
        assert "[1]" in response_with_citations
        assert len(formatted_sources) == 1
    
    @pytest.mark.asyncio
    async def test_prompt_selection(self, rag_service):
        """Test automatic prompt selection based on query."""
        # Arrange
        simple_query = "What is AI?"
        complex_query = "Explain the implications of AI on society and compare it to previous technological revolutions"
        
        context_docs = [
            {
                "content": "Test content",
                "score": 0.8,
                "document_id": "doc1",
                "source": "Test"
            }
        ]
        
        # Act - simple query
        simple_prompt = rag_service._select_prompt_template(
            query=simple_query,
            context_docs=context_docs,
            chat_history=None
        )
        
        # Act - complex query
        complex_prompt = rag_service._select_prompt_template(
            query=complex_query,
            context_docs=context_docs,
            chat_history=None
        )
        
        # Assert
        assert rag_service.rag_prompt_template.template in simple_prompt
        assert rag_service.reasoning_prompt_template.template in complex_prompt
    
    @pytest.mark.asyncio
    async def test_rag_service_fallback(self, rag_service):
        """Test fallback when LLM service is unavailable."""
        # Arrange
        rag_service.llm_service.is_available.return_value = False
        
        # Act
        response = await rag_service.generate_rag_response(
            user_id="test_user",
            query="Test query"
        )
        
        # Assert - Should still return a response (fallback)
        assert response["content"] is not None
        assert "I apologize" in response["content"] or "Test response" in response["content"]
    
    @pytest.mark.asyncio
    async def test_end_to_end_rag_workflow(self, rag_service):
        """Test complete RAG workflow."""
        # Arrange
        user_id = "test_user_123"
        query = "What are the main applications of machine learning?"
        chat_history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        
        # Act - Full RAG pipeline
        context_docs = await rag_service.retrieve_context(
            user_id=user_id,
            query=query,
            n_results=3
        )
        
        formatted_context = rag_service.format_context_for_prompt(context_docs)
        formatted_history = rag_service.format_chat_history_for_prompt(chat_history)
        
        response = await rag_service.generate_rag_response(
            user_id=user_id,
            query=query,
            chat_history=chat_history,
            include_sources=True
        )
        
        # Assert
        assert len(context_docs) > 0
        assert len(formatted_context) > 0
        assert len(formatted_history) > 0
        assert response["content"] is not None
        assert response["context_used"] is True
        assert "sources" in response
        
        # Verify response contains expected structure
        assert isinstance(response["sources"], list)
        if response["sources"]:
            source = response["sources"][0]
            assert "document_id" in source
            assert "source" in source


if __name__ == "__main__":
    # Run tests
    import sys
    sys.exit(pytest.main([__file__, "-v"]))