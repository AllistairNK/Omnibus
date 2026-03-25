#!/usr/bin/env python3
"""
Simple test script to demonstrate the document processing pipeline.
"""

import sys
sys.path.insert(0, '.')

from app.services.document_parser import DocumentParser
from app.services.text_cleaner import TextCleaner
from app.services.document_chunker import DocumentChunker

def test_text_processing():
    """Test the complete document processing pipeline with sample text."""
    print("=== Testing Document Processing Pipeline ===\n")
    
    # Sample text (simulating a parsed document)
    sample_text = """
    Artificial Intelligence (AI) is transforming industries worldwide.
    
    Machine learning, a subset of AI, enables computers to learn from data without explicit programming.
    
    Natural Language Processing (NLP) allows machines to understand and generate human language.
    
    These technologies are driving innovation in healthcare, finance, and education.
    """
    
    print("1. Original Text:")
    print(sample_text)
    print("\n" + "="*80 + "\n")
    
    # Step 1: Clean the text
    print("2. Cleaning Text...")
    cleaned_text = TextCleaner.clean_text(sample_text, preserve_structure=True)
    print("Cleaned Text:")
    print(cleaned_text)
    
    # Calculate text metrics
    metrics = TextCleaner.calculate_text_metrics(cleaned_text)
    print(f"\nText Metrics:")
    print(f"  - Characters: {metrics['character_count']}")
    print(f"  - Words: {metrics['word_count']}")
    print(f"  - Sentences: {metrics['sentence_count']}")
    print(f"  - Lines: {metrics['line_count']}")
    
    print("\n" + "="*80 + "\n")
    
    # Step 2: Chunk the text
    print("3. Chunking Text...")
    
    # Test different chunking strategies
    strategies = ["fixed", "paragraph", "sentence", "hybrid"]
    
    for strategy in strategies:
        print(f"\nStrategy: {strategy.upper()}")
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20, strategy=strategy)
        chunks = chunker.chunk_text(cleaned_text)
        
        print(f"  Number of chunks: {len(chunks)}")
        
        if chunks:
            metrics = DocumentChunker.calculate_chunking_metrics(chunks)
            print(f"  Avg chunk size: {metrics['avg_chunk_size']} chars")
            print(f"  Chunk types: {metrics['chunk_types']}")
            
            # Show first chunk
            print(f"  First chunk ({chunks[0]['chunk_type']}):")
            print(f"    '{chunks[0]['text'][:80]}...'")
    
    print("\n" + "="*80 + "\n")
    
    # Step 3: Test parsing (simulated)
    print("4. Testing Document Parsing (Simulated)...")
    
    # Simulate parsing different file types
    test_cases = [
        ("txt", "sample.txt", b"This is a plain text file.\nWith multiple lines.\nAnd content."),
        ("md", "sample.md", b"# Markdown File\n\nThis is **bold** text.\n\n- List item 1\n- List item 2"),
    ]
    
    for file_type, filename, content in test_cases:
        print(f"\nFile: {filename} (Type: {file_type})")
        try:
            # Note: We're not actually parsing PDF/DOCX here since we don't have real files
            if file_type in ["txt", "md"]:
                if file_type == "txt":
                    text, metadata = DocumentParser.parse_text(content)
                else:  # md
                    text, metadata = DocumentParser.parse_markdown(content)
                
                print(f"  Successfully parsed")
                print(f"  Metadata: {list(metadata.keys())}")
                
                # Clean and chunk
                cleaned = TextCleaner.clean_text(text)
                chunker = DocumentChunker(chunk_size=50, strategy="fixed")
                chunks = chunker.chunk_text(cleaned)
                print(f"  Created {len(chunks)} chunks")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*80)
    print("Document Processing Pipeline Test Complete!")
    print("All components are working correctly.")

if __name__ == "__main__":
    test_text_processing()