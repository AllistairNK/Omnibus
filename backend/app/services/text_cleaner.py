"""
Text cleaning and normalization utilities for document processing.

Provides functions to clean extracted text by removing excessive whitespace,
normalizing characters, and preparing text for chunking and embedding.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TextCleaner:
    """Utilities for cleaning and normalizing extracted text."""
    
    @staticmethod
    def clean_text(text: str, preserve_structure: bool = True) -> str:
        """
        Clean extracted text by removing excessive whitespace and normalizing.
        
        Args:
            text: Raw extracted text
            preserve_structure: Whether to preserve paragraph breaks and structure
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove null characters and other control characters (except newlines/tabs)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line endings to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        if preserve_structure:
            # Preserve paragraph breaks (multiple newlines)
            # Replace 3+ newlines with 2 newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # Clean up within paragraphs
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                # Remove extra spaces within line
                line = re.sub(r'[ \t]+', ' ', line.strip())
                if line:  # Keep non-empty lines
                    cleaned_lines.append(line)
            
            # Rejoin with preserved paragraph breaks
            text = '\n'.join(cleaned_lines)
        else:
            # Remove all newlines and excessive spaces
            text = re.sub(r'\s+', ' ', text).strip()
        
        # Normalize Unicode characters (optional - could expand to handle more)
        # Replace curly quotes with straight quotes
        text = text.replace('"', '"').replace("'", "'")
        text = text.replace('"', '"').replace("'", "'")
        
        # Remove excessive punctuation (optional)
        # text = re.sub(r'[.!?]{3,}', '...', text)
        
        return text
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Normalize line endings
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # Remove trailing/leading whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences using simple heuristic.
        
        Note: This is a basic implementation. For production use,
        consider using NLTK or spaCy for better sentence segmentation.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        # Basic sentence splitting on punctuation
        # This handles common cases but may fail with abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @staticmethod
    def calculate_text_metrics(text: str) -> Dict[str, any]:
        """
        Calculate metrics about the text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with text metrics
        """
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "line_count": 0,
                "avg_word_length": 0,
                "avg_sentence_length": 0,
            }
        
        # Basic metrics
        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        
        # Sentence count (approximate)
        sentences = TextCleaner.split_into_sentences(text)
        sentence_count = len(sentences)
        
        # Average lengths
        avg_word_length = character_count / max(word_count, 1)
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        return {
            "character_count": character_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "line_count": line_count,
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
        }
    
    @staticmethod
    def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
        """
        Extract potential key phrases from text (simple heuristic).
        
        Args:
            text: Input text
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of key phrases
        """
        # Simple implementation: extract capitalized phrases and frequent words
        # For production, consider using RAKE, YAKE, or other keyphrase extraction libraries
        
        # Find capitalized phrases (excluding start of sentences)
        sentences = TextCleaner.split_into_sentences(text)
        key_phrases = []
        
        for sentence in sentences:
            # Find proper nouns/important terms (words starting with capital in middle of sentence)
            words = sentence.split()
            for i, word in enumerate(words):
                if i > 0 and word[0].isupper() and len(word) > 2:
                    # Check if it's part of a multi-word phrase
                    phrase = word
                    # Look ahead for continuation
                    j = i + 1
                    while j < len(words) and words[j][0].isupper():
                        phrase += " " + words[j]
                        j += 1
                    if phrase not in key_phrases:
                        key_phrases.append(phrase)
        
        # Limit number of phrases
        return key_phrases[:max_phrases]
    
    @staticmethod
    def prepare_for_chunking(text: str, min_chunk_size: int = 100) -> Tuple[str, List[str]]:
        """
        Prepare text for chunking by cleaning and optionally pre-segmenting.
        
        Args:
            text: Raw text
            min_chunk_size: Minimum chunk size in characters
            
        Returns:
            Tuple of (cleaned_text, suggested_breakpoints)
        """
        # Clean the text
        cleaned_text = TextCleaner.clean_text(text, preserve_structure=True)
        
        # Find natural breakpoints (paragraphs, headings, etc.)
        breakpoints = []
        
        # Use paragraph breaks as natural chunk boundaries
        paragraphs = cleaned_text.split('\n\n')
        if len(paragraphs) > 1:
            # Calculate cumulative positions
            pos = 0
            for para in paragraphs[:-1]:  # All but last paragraph
                pos += len(para) + 2  # +2 for \n\n
                if pos > min_chunk_size:
                    breakpoints.append(pos)
        
        # Also consider sentence boundaries for very long paragraphs
        if not breakpoints:
            sentences = TextCleaner.split_into_sentences(cleaned_text)
            pos = 0
            for sent in sentences[:-1]:
                pos += len(sent) + 1  # +1 for space
                if pos > min_chunk_size:
                    breakpoints.append(pos)
        
        return cleaned_text, breakpoints