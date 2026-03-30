-- Storage RLS policies for the 'documents' bucket
-- This ensures authenticated users can upload files to the bucket

-- Enable RLS on storage.objects (should already be enabled by Supabase)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy for SELECT: users can see files they uploaded (owner)
CREATE POLICY "Users can view their own files"
ON storage.objects FOR SELECT
USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Policy for INSERT: authenticated users can upload files to their own folder
CREATE POLICY "Authenticated users can upload files"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'documents' AND auth.role() = 'authenticated');

-- Policy for UPDATE: users can update their own files
CREATE POLICY "Users can update their own files"
ON storage.objects FOR UPDATE
USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Policy for DELETE: users can delete their own files
CREATE POLICY "Users can delete their own files"
ON storage.objects FOR DELETE
USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Comment
COMMENT ON POLICY "Users can view their own files" ON storage.objects IS 'Allow users to view files they uploaded in the documents bucket';
COMMENT ON POLICY "Authenticated users can upload files" ON storage.objects IS 'Allow authenticated users to upload files to documents bucket';
COMMENT ON POLICY "Users can update their own files" ON storage.objects IS 'Allow users to update their own files';
COMMENT ON POLICY "Users can delete their own files" ON storage.objects IS 'Allow users to delete their own files';