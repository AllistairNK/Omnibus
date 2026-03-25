-- Migration to add additional metadata columns to document_chunks table
-- Required for Task 3.2: Document Processing

-- Add new columns to document_chunks table
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS start_position INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS end_position INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS size_chars INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS size_words INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS chunk_type VARCHAR(50) DEFAULT 'fixed';

-- Update existing rows to have user_id (derive from document)
UPDATE document_chunks dc
SET user_id = d.user_id
FROM documents d
WHERE dc.document_id = d.id
  AND dc.user_id IS NULL;

-- Make user_id NOT NULL after populating
ALTER TABLE document_chunks
ALTER COLUMN user_id SET NOT NULL;

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_user_id ON document_chunks(user_id);

-- Create index on chunk_type for filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_type ON document_chunks(chunk_type);

-- Add comment explaining the new columns
COMMENT ON COLUMN document_chunks.user_id IS 'User who owns this chunk (denormalized from document for performance)';
COMMENT ON COLUMN document_chunks.start_position IS 'Start position of chunk in original document (character offset)';
COMMENT ON COLUMN document_chunks.end_position IS 'End position of chunk in original document (character offset)';
COMMENT ON COLUMN document_chunks.size_chars IS 'Size of chunk in characters';
COMMENT ON COLUMN document_chunks.size_words IS 'Size of chunk in words';
COMMENT ON COLUMN document_chunks.chunk_type IS 'Type of chunking used (fixed, paragraph, sentence, hybrid)';