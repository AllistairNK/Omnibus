-- Sample data for development and testing
-- This migration adds sample users, API keys, and documents for testing

-- Insert sample users (IDs match Supabase Auth users in development)
INSERT INTO users (id, email, created_at) VALUES
    ('11111111-1111-1111-1111-111111111111', 'test@example.com', NOW()),
    ('22222222-2222-2222-2222-222222222222', 'admin@example.com', NOW())
ON CONFLICT (id) DO NOTHING;

-- Insert sample API keys (encrypted with dummy values)
INSERT INTO api_keys (id, user_id, provider, encrypted_key, is_active) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'openai', 'encrypted_dummy_key_1', true),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'anthropic', 'encrypted_dummy_key_2', true),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222', 'openai', 'encrypted_dummy_key_3', true)
ON CONFLICT (id) DO NOTHING;

-- Insert sample documents
INSERT INTO documents (id, user_id, filename, file_path, file_size, file_type, status, chunk_count) VALUES
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', '11111111-1111-1111-1111-111111111111', 'sample.pdf', 'uploads/sample.pdf', 102400, 'pdf', 'processed', 5),
    ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '11111111-1111-1111-1111-111111111111', 'notes.txt', 'uploads/notes.txt', 5120, 'txt', 'uploaded', 0),
    ('ffffffff-ffff-ffff-ffff-ffffffffffff', '22222222-2222-2222-2222-222222222222', 'report.docx', 'uploads/report.docx', 204800, 'docx', 'processing', 0)
ON CONFLICT (id) DO NOTHING;

-- Insert sample document chunks
INSERT INTO document_chunks (id, document_id, chunk_index, content) VALUES
    ('aaaaaaaa-0000-0000-0000-000000000001', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 1, 'This is the first chunk of sample document.'),
    ('aaaaaaaa-0000-0000-0000-000000000002', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 2, 'This is the second chunk with more content.'),
    ('aaaaaaaa-0000-0000-0000-000000000003', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 3, 'Third chunk containing important information.'),
    ('aaaaaaaa-0000-0000-0000-000000000004', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 4, 'Fourth chunk with additional details.'),
    ('aaaaaaaa-0000-0000-0000-000000000005', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 5, 'Final chunk of the sample document.')
ON CONFLICT (id) DO NOTHING;

-- Insert sample chats
INSERT INTO chats (id, user_id, title, model_used) VALUES
    ('cccccccc-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Sample Chat about AI', 'gpt-4'),
    ('cccccccc-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Document Analysis', 'claude-3')
ON CONFLICT (id) DO NOTHING;

-- Insert sample messages
INSERT INTO messages (id, chat_id, role, content, timestamp) VALUES
    ('mmmmmmmm-0000-0000-0000-000000000001', 'cccccccc-0000-0000-0000-000000000001', 'user', 'Hello, can you explain RAG?', NOW() - INTERVAL '1 hour'),
    ('mmmmmmmm-0000-0000-0000-000000000002', 'cccccccc-0000-0000-0000-000000000001', 'assistant', 'RAG stands for Retrieval-Augmented Generation...', NOW() - INTERVAL '55 minutes'),
    ('mmmmmmmm-0000-0000-0000-000000000003', 'cccccccc-0000-0000-0000-000000000001', 'user', 'How does it work with documents?', NOW() - INTERVAL '50 minutes'),
    ('mmmmmmmm-0000-0000-0000-000000000004', 'cccccccc-0000-0000-0000-000000000001', 'assistant', 'RAG works by retrieving relevant document chunks...', NOW() - INTERVAL '45 minutes')
ON CONFLICT (id) DO NOTHING;