"""
Unit tests for document chunking strategies.
"""

import pytest

from app.services.document_chunker import DocumentChunker


class TestDocumentChunker:
    """Test document chunking functionality."""
    
    def test_init_valid(self):
        """Test chunker initialization with valid parameters."""
        chunker = DocumentChunker(
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=50,
            strategy="fixed"
        )
        
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 200
        assert chunker.min_chunk_size == 50
        assert chunker.strategy == "fixed"
    
    def test_init_invalid_overlap(self):
        """Test chunker initialization with invalid overlap."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            DocumentChunker(chunk_size=500, chunk_overlap=500)
    
    def test_chunk_fixed_size_basic(self):
        """Test fixed-size chunking with simple text."""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10, strategy="fixed")
        
        text = "This is a test document that needs to be chunked into smaller pieces for processing."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "chunk_index" in chunk
            assert "size_chars" in chunk
            assert chunk["size_chars"] <= 50 + 20  # Allow some flexibility for boundary finding
    
    def test_chunk_fixed_size_empty(self):
        """Test fixed-size chunking with empty text."""
        chunker = DocumentChunker(strategy="fixed")
        
        chunks = chunker.chunk_text("")
        
        assert chunks == []
    
    def test_chunk_fixed_size_small_text(self):
        """Test fixed-size chunking with text smaller than chunk size."""
        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200, strategy="fixed")
        
        text = "Short text"
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["size_chars"] == len(text)
    
    def test_chunk_by_paragraph(self):
        """Test paragraph-based chunking."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20, strategy="paragraph")
        
        text = """First paragraph with some content.
        
        Second paragraph that is a bit longer and contains more information.
        
        Third paragraph."""
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["chunk_type"] == "paragraph"
    
    def test_chunk_by_sentence(self):
        """Test sentence-based chunking."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20, strategy="sentence")
        
        text = "First sentence. Second sentence is longer. Third sentence. Fourth."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["chunk_type"] == "sentence"
    
    def test_chunk_hybrid(self):
        """Test hybrid chunking strategy."""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10, strategy="hybrid")
        
        text = """Short paragraph.
        
        This is a much longer paragraph that will likely need to be split into multiple chunks because it exceeds the chunk size limit by a significant margin.
        
        Another short one."""
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        # Should have mixed chunk types
        chunk_types = [chunk.get("chunk_type") for chunk in chunks]
        assert "paragraph" in chunk_types or "hybrid_fixed" in chunk_types
    
    def test_chunk_unknown_strategy_fallback(self):
        """Test chunking with unknown strategy falls back to fixed."""
        chunker = DocumentChunker(strategy="unknown")
        
        text = "Test text for chunking."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1  # Should still work with fallback
    
    def test_find_sentence_boundary(self):
        """Test finding sentence boundaries."""
        chunker = DocumentChunker()
        
        text = "First sentence. Second sentence! Third sentence? Fourth."
        
        # Test boundary near position 30
        boundary = chunker._find_sentence_boundary(text, 30)
        
        # Should find a sentence boundary
        assert boundary > 0
        # Boundary should be at a sentence ending
        assert text[boundary-2:boundary] in [". ", "! ", "? "]
    
    def test_create_chunk_dict(self):
        """Test chunk dictionary creation."""
        chunker = DocumentChunker()
        
        chunk_dict = chunker._create_chunk_dict(
            text="Test chunk",
            start_pos=0,
            end_pos=10,
            chunk_index=0,
            metadata={"author": "Test"},
            chunk_type="test"
        )
        
        assert chunk_dict["text"] == "Test chunk"
        assert chunk_dict["start_pos"] == 0
        assert chunk_dict["end_pos"] == 10
        assert chunk_dict["chunk_index"] == 0
        assert chunk_dict["size_chars"] == 10
        assert chunk_dict["size_words"] == 2
        assert chunk_dict["chunk_type"] == "test"
        assert "metadata" in chunk_dict
    
    def test_calculate_chunking_metrics(self):
        """Test chunking metrics calculation."""
        chunks = [
            {"size_chars": 100, "chunk_type": "fixed"},
            {"size_chars": 150, "chunk_type": "fixed"},
            {"size_chars": 80, "chunk_type": "paragraph"},
        ]
        
        metrics = DocumentChunker.calculate_chunking_metrics(chunks)
        
        assert metrics["total_chunks"] == 3
        assert metrics["avg_chunk_size"] == 110.0  # (100+150+80)/3
        assert metrics["min_chunk_size"] == 80
        assert metrics["max_chunk_size"] == 150
        assert metrics["total_characters"] == 330
        assert metrics["chunk_types"]["fixed"] == 2
        assert metrics["chunk_types"]["paragraph"] == 1
    
    def test_calculate_chunking_metrics_empty(self):
        """Test chunking metrics with empty chunks list."""
        metrics = DocumentChunker.calculate_chunking_metrics([])
        
        assert metrics["total_chunks"] == 0
        assert metrics["avg_chunk_size"] == 0
        assert metrics["min_chunk_size"] == 0
        assert metrics["max_chunk_size"] == 0
        assert metrics["total_characters"] == 0
        assert metrics["chunk_types"] == {}