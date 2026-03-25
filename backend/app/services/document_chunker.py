"""
Document chunking strategies for splitting text into manageable pieces.

Provides multiple chunking strategies:
1. Fixed-size chunking with overlap
2. Semantic chunking (by paragraphs, sentences)
3. Hybrid approach
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from app.services.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Strategies for chunking documents into smaller pieces."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 50,
        strategy: str = "fixed"
    ):
        """
        Initialize chunker with configuration.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            min_chunk_size: Minimum acceptable chunk size
            strategy: Chunking strategy ("fixed", "paragraph", "sentence", "hybrid")
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.strategy = strategy
        
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Chunk text based on selected strategy.
        
        Args:
            text: Cleaned text to chunk
            metadata: Optional document metadata
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text:
            return []
        
        if self.strategy == "fixed":
            return self._chunk_fixed_size(text, metadata)
        elif self.strategy == "paragraph":
            return self._chunk_by_paragraph(text, metadata)
        elif self.strategy == "sentence":
            return self._chunk_by_sentence(text, metadata)
        elif self.strategy == "hybrid":
            return self._chunk_hybrid(text, metadata)
        else:
            logger.warning(f"Unknown strategy '{self.strategy}', falling back to fixed")
            return self._chunk_fixed_size(text, metadata)
    
    def _chunk_fixed_size(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Fixed-size chunking with overlap.
        
        Splits text into chunks of approximately chunk_size characters,
        with chunk_overlap characters of overlap between consecutive chunks.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
            
        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If we're near the end, extend to include remaining text
            if end >= text_length:
                end = text_length
            else:
                # Try to end at a sentence boundary if possible
                sentence_end = self._find_sentence_boundary(text, end)
                if sentence_end > start + self.min_chunk_size:
                    end = sentence_end
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk_dict(
                    text=chunk_text,
                    start_pos=start,
                    end_pos=end,
                    chunk_index=len(chunks),
                    metadata=metadata
                ))
            
            # Move start position for next chunk (with overlap)
            start = end - self.chunk_overlap
            
            # Ensure we make progress
            if start <= chunks[-1]["start_pos"] if chunks else 0:
                start = end
        
        return chunks
    
    def _chunk_by_paragraph(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Chunk by paragraphs, combining small paragraphs.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
            
        Returns:
            List of chunks
        """
        # Split by paragraph breaks
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If adding this paragraph would exceed chunk size and we have content
            if current_size + para_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(self._create_chunk_dict(
                    text=chunk_text,
                    start_pos=0,  # Would need actual positions for accuracy
                    end_pos=0,
                    chunk_index=len(chunks),
                    metadata=metadata,
                    chunk_type="paragraph"
                ))
                
                # Start new chunk with overlap from previous chunk
                current_chunk = []
                current_size = 0
                
                # Add overlap from previous chunk if needed
                if self.chunk_overlap > 0 and chunks:
                    last_chunk = chunks[-1]["text"]
                    overlap_text = last_chunk[-self.chunk_overlap:]
                    if overlap_text:
                        current_chunk.append(overlap_text)
                        current_size = len(overlap_text)
            
            # Add paragraph to current chunk
            current_chunk.append(para)
            current_size += para_size
        
        # Add final chunk if any content remains
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(self._create_chunk_dict(
                text=chunk_text,
                start_pos=0,
                end_pos=0,
                chunk_index=len(chunks),
                metadata=metadata,
                chunk_type="paragraph"
            ))
        
        return chunks
    
    def _chunk_by_sentence(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Chunk by sentences, combining small sentences.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
            
        Returns:
            List of chunks
        """
        sentences = TextCleaner.split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sent in sentences:
            sent_size = len(sent)
            
            # If adding this sentence would exceed chunk size and we have content
            if current_size + sent_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(self._create_chunk_dict(
                    text=chunk_text,
                    start_pos=0,
                    end_pos=0,
                    chunk_index=len(chunks),
                    metadata=metadata,
                    chunk_type="sentence"
                ))
                
                # Start new chunk with overlap
                current_chunk = []
                current_size = 0
                
                # Add overlap from previous chunk if needed
                if self.chunk_overlap > 0 and chunks:
                    last_chunk = chunks[-1]["text"]
                    overlap_words = last_chunk.split()[-10:]  # Approximate overlap
                    overlap_text = ' '.join(overlap_words)
                    if overlap_text:
                        current_chunk.append(overlap_text)
                        current_size = len(overlap_text)
            
            # Add sentence to current chunk
            current_chunk.append(sent)
            current_size += sent_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(self._create_chunk_dict(
                text=chunk_text,
                start_pos=0,
                end_pos=0,
                chunk_index=len(chunks),
                metadata=metadata,
                chunk_type="sentence"
            ))
        
        return chunks
    
    def _chunk_hybrid(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Hybrid chunking: try to chunk by paragraphs first, fall back to fixed.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
            
        Returns:
            List of chunks
        """
        # First try paragraph chunking
        paragraph_chunks = self._chunk_by_paragraph(text, metadata)
        
        # Check if any chunks are too large
        large_chunks = [chunk for chunk in paragraph_chunks if len(chunk["text"]) > self.chunk_size * 1.5]
        
        if not large_chunks:
            return paragraph_chunks
        
        # For chunks that are too large, apply fixed-size chunking
        final_chunks = []
        for chunk in paragraph_chunks:
            if len(chunk["text"]) > self.chunk_size * 1.5:
                # Re-chunk this large paragraph
                sub_chunks = self._chunk_fixed_size(chunk["text"], metadata)
                # Update metadata for sub-chunks
                for i, sub_chunk in enumerate(sub_chunks):
                    sub_chunk["parent_chunk_index"] = chunk["chunk_index"]
                    sub_chunk["chunk_index"] = len(final_chunks) + i
                    sub_chunk["chunk_type"] = "hybrid_fixed"
                final_chunks.extend(sub_chunks)
            else:
                chunk["chunk_index"] = len(final_chunks)
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """
        Find a good sentence boundary near the given position.
        
        Args:
            text: Full text
            position: Target position
            
        Returns:
            Adjusted position at sentence boundary
        """
        # Look for sentence endings within a window
        window_size = 100
        start = max(0, position - window_size)
        end = min(len(text), position + window_size)
        
        window = text[start:end]
        
        # Look for sentence endings (. ! ?) followed by space
        for match in re.finditer(r'[.!?]\s+', window):
            # Position relative to full text
            match_pos = start + match.end()
            
            # Check if this is a reasonable boundary
            if match_pos > position - window_size // 2:
                return match_pos
        
        # If no good boundary found, return original position
        return position
    
    def _create_chunk_dict(
        self,
        text: str,
        start_pos: int,
        end_pos: int,
        chunk_index: int,
        metadata: Optional[Dict] = None,
        chunk_type: str = "fixed"
    ) -> Dict[str, any]:
        """
        Create standardized chunk dictionary.
        
        Args:
            text: Chunk text
            start_pos: Start position in original text
            end_pos: End position in original text
            chunk_index: Index of this chunk
            metadata: Document metadata
            chunk_type: Type of chunking used
            
        Returns:
            Chunk dictionary
        """
        chunk_data = {
            "text": text,
            "chunk_index": chunk_index,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "size_chars": len(text),
            "size_words": len(text.split()),
            "chunk_type": chunk_type,
            "metadata": metadata or {},
        }
        
        # Add document metadata if available
        if metadata:
            chunk_data["document_metadata"] = {
                k: v for k, v in metadata.items()
                if k not in ["text", "chunks"]
            }
        
        return chunk_data
    
    @classmethod
    def calculate_chunking_metrics(cls, chunks: List[Dict]) -> Dict[str, any]:
        """
        Calculate metrics about chunking results.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with chunking metrics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "total_characters": 0,
                "chunk_types": {},
            }
        
        sizes = [chunk["size_chars"] for chunk in chunks]
        chunk_types = {}
        
        for chunk in chunks:
            chunk_type = chunk.get("chunk_type", "unknown")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": round(sum(sizes) / len(sizes), 2),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "total_characters": sum(sizes),
            "chunk_types": chunk_types,
        }