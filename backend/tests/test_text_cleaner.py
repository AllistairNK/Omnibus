"""
Unit tests for text cleaning utilities.
"""

import pytest

from app.services.text_cleaner import TextCleaner


class TestTextCleaner:
    """Test text cleaning functionality."""
    
    def test_clean_text_preserve_structure(self):
        """Test cleaning text while preserving structure."""
        dirty_text = """   Hello   world!   
        
        This   is   a   test.   
        
        With   multiple   paragraphs.   """
        
        cleaned = TextCleaner.clean_text(dirty_text, preserve_structure=True)
        
        # Should preserve paragraph breaks
        assert "\n\n" in cleaned
        # Should remove extra spaces
        assert "  " not in cleaned
        # Should trim lines
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")
    
    def test_clean_text_no_structure(self):
        """Test cleaning text without preserving structure."""
        dirty_text = """   Hello   world!   
        
        This   is   a   test.   """
        
        cleaned = TextCleaner.clean_text(dirty_text, preserve_structure=False)
        
        # Should be a single line
        assert "\n" not in cleaned
        # Should have single spaces
        assert "  " not in cleaned
        assert cleaned == "Hello world! This is a test."
    
    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        assert TextCleaner.clean_text("") == ""
        assert TextCleaner.clean_text("   ") == ""
    
    def test_clean_text_control_characters(self):
        """Test cleaning text with control characters."""
        dirty_text = "Hello\x00world\x07\x08test"
        
        cleaned = TextCleaner.clean_text(dirty_text)
        
        # Control characters should be removed
        assert "\x00" not in cleaned
        assert "\x07" not in cleaned
        assert "\x08" not in cleaned
        assert "Helloworldtest" in cleaned
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text = "Hello\tworld\n\nThis  is   a    test\r\nwith\rvarious whitespace"
        
        normalized = TextCleaner.normalize_whitespace(text)
        
        # Tabs should be replaced with spaces
        assert "\t" not in normalized
        # Multiple spaces should be single spaces
        assert "  " not in normalized
        # Line endings should be normalized to \n
        assert "\r\n" not in normalized
        assert "\r" not in normalized
        # Empty lines should be removed
        assert "\n\n" not in normalized
    
    def test_split_into_sentences(self):
        """Test sentence splitting."""
        text = "Hello world! This is a test. How are you? I'm fine."
        
        sentences = TextCleaner.split_into_sentences(text)
        
        assert len(sentences) == 4
        assert sentences[0] == "Hello world!"
        assert sentences[1] == "This is a test."
        assert sentences[2] == "How are you?"
        assert sentences[3] == "I'm fine."
    
    def test_split_into_sentences_empty(self):
        """Test sentence splitting with empty text."""
        assert TextCleaner.split_into_sentences("") == []
        assert TextCleaner.split_into_sentences("   ") == []
    
    def test_calculate_text_metrics(self):
        """Test text metrics calculation."""
        text = "Hello world! This is a test.\nIt has multiple lines."
        
        metrics = TextCleaner.calculate_text_metrics(text)
        
        assert metrics["character_count"] == len(text)
        assert metrics["word_count"] == 9  # Hello, world!, This, is, a, test., It, has, multiple, lines.
        assert metrics["line_count"] == 2
        assert metrics["sentence_count"] == 2
        assert metrics["avg_word_length"] > 0
        assert metrics["avg_sentence_length"] > 0
    
    def test_calculate_text_metrics_empty(self):
        """Test text metrics with empty text."""
        metrics = TextCleaner.calculate_text_metrics("")
        
        assert metrics["character_count"] == 0
        assert metrics["word_count"] == 0
        assert metrics["line_count"] == 1  # Empty string has 1 line
        assert metrics["sentence_count"] == 0
        assert metrics["avg_word_length"] == 0
        assert metrics["avg_sentence_length"] == 0
    
    def test_extract_key_phrases(self):
        """Test key phrase extraction."""
        text = "The United Nations held a meeting in New York City. President Biden attended."
        
        phrases = TextCleaner.extract_key_phrases(text, max_phrases=5)
        
        # Should extract capitalized phrases
        assert any("United Nations" in phrase for phrase in phrases)
        assert any("New York City" in phrase for phrase in phrases)
        assert any("President Biden" in phrase for phrase in phrases)
    
    def test_prepare_for_chunking(self):
        """Test text preparation for chunking."""
        text = """First paragraph.
        
        Second paragraph is longer and has more content.
        
        Third paragraph."""
        
        cleaned_text, breakpoints = TextCleaner.prepare_for_chunking(text, min_chunk_size=20)
        
        # Should clean the text
        assert cleaned_text == "First paragraph.\n\nSecond paragraph is longer and has more content.\n\nThird paragraph."
        # Should suggest breakpoints at paragraph boundaries
        assert len(breakpoints) > 0