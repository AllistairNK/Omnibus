"""
Unit tests for document parsing utilities.
"""

import pytest
from unittest.mock import patch, MagicMock
import io

from app.services.document_parser import DocumentParser


class TestDocumentParser:
    """Test document parsing functionality."""
    
    def test_parse_text_success(self):
        """Test parsing plain text file."""
        text_content = b"Hello, world!\nThis is a test document.\nWith multiple lines."
        
        text, metadata = DocumentParser.parse_text(text_content)
        
        assert "Hello, world!" in text
        assert metadata["encoding"] == "utf-8"
        assert metadata["character_count"] > 0
        assert metadata["line_count"] == 3
    
    def test_parse_text_latin1(self):
        """Test parsing text with latin-1 encoding."""
        # Create latin-1 encoded text
        text_content = "Café avec des accents".encode('latin-1')
        
        text, metadata = DocumentParser.parse_text(text_content, encoding="latin-1")
        
        assert "Café" in text
        assert metadata["encoding"] == "latin-1"
    
    def test_parse_markdown(self):
        """Test parsing markdown file."""
        md_content = b"""# Title
        
This is **bold** text.

- List item 1
- List item 2

`code block`
"""
        
        text, metadata = DocumentParser.parse_markdown(md_content)
        
        assert "Title" in text
        assert "bold" in text
        assert metadata["heading_count"] == 1
        assert metadata["line_count"] > 0
    
    @patch('app.services.document_parser.PdfReader')
    def test_parse_pdf_success(self, mock_pdf_reader):
        """Test parsing PDF file."""
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader.metadata = MagicMock()
        mock_reader.is_encrypted = False
        mock_pdf_reader.return_value = mock_reader
        
        pdf_content = b"fake pdf content"
        
        text, metadata = DocumentParser.parse_pdf(pdf_content)
        
        assert "Page 1 content" in text
        assert "Page 2 content" in text
        assert metadata["page_count"] == 2
        assert metadata["has_encryption"] is False
    
    @patch('app.services.document_parser.Document')
    def test_parse_docx_success(self, mock_document):
        """Test parsing DOCX file."""
        # Mock DOCX document
        mock_doc = MagicMock()
        
        # Mock paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_para1, mock_para2]
        
        # Mock tables
        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_cell1 = MagicMock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = MagicMock()
        mock_cell2.text = "Cell 2"
        mock_row.cells = [mock_cell1, mock_cell2]
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]
        
        # Mock core properties
        mock_doc.core_properties = MagicMock()
        mock_doc.core_properties.author = "Test Author"
        mock_doc.core_properties.title = "Test Document"
        
        mock_document.return_value = mock_doc
        
        docx_content = b"fake docx content"
        
        text, metadata = DocumentParser.parse_docx(docx_content)
        
        assert "First paragraph" in text
        assert "Second paragraph" in text
        assert "Cell 1 | Cell 2" in text
        assert metadata["paragraph_count"] == 2
        assert metadata["table_count"] == 1
        assert metadata["author"] == "Test Author"
    
    def test_parse_document_unsupported_type(self):
        """Test parsing unsupported file type raises error."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            DocumentParser.parse_document(b"content", "exe", "test.exe")
    
    def test_parse_document_pdf(self):
        """Test parse_document with PDF type."""
        with patch.object(DocumentParser, 'parse_pdf') as mock_parse_pdf:
            mock_parse_pdf.return_value = ("parsed text", {"page_count": 1})
            
            text, metadata = DocumentParser.parse_document(
                b"pdf content", "pdf", "test.pdf"
            )
            
            mock_parse_pdf.assert_called_once_with(b"pdf content")
            assert text == "parsed text"
            assert metadata["page_count"] == 1
    
    def test_parse_document_docx(self):
        """Test parse_document with DOCX type."""
        with patch.object(DocumentParser, 'parse_docx') as mock_parse_docx:
            mock_parse_docx.return_value = ("parsed text", {"paragraph_count": 2})
            
            text, metadata = DocumentParser.parse_document(
                b"docx content", "docx", "test.docx"
            )
            
            mock_parse_docx.assert_called_once_with(b"docx content")
            assert text == "parsed text"
            assert metadata["paragraph_count"] == 2
    
    def test_parse_document_txt(self):
        """Test parse_document with TXT type."""
        with patch.object(DocumentParser, 'parse_text') as mock_parse_text:
            mock_parse_text.return_value = ("parsed text", {"encoding": "utf-8"})
            
            text, metadata = DocumentParser.parse_document(
                b"txt content", "txt", "test.txt"
            )
            
            mock_parse_text.assert_called_once_with(b"txt content")
            assert text == "parsed text"
            assert metadata["encoding"] == "utf-8"
    
    def test_parse_document_md(self):
        """Test parse_document with MD type."""
        with patch.object(DocumentParser, 'parse_markdown') as mock_parse_md:
            mock_parse_md.return_value = ("parsed text", {"heading_count": 1})
            
            text, metadata = DocumentParser.parse_document(
                b"md content", "md", "test.md"
            )
            
            mock_parse_md.assert_called_once_with(b"md content")
            assert text == "parsed text"
            assert metadata["heading_count"] == 1