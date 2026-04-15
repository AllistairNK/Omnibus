# AI Chatbot with RAG - API Documentation

## Overview

This document provides comprehensive API documentation for the AI Chatbot with RAG backend. The API follows RESTful conventions and uses JSON for request/response payloads. All endpoints are versioned under `/api/v1`.

## Base URL

- **Local Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-backend-domain.com/api/v1`

## Authentication

Most endpoints require authentication using JWT (JSON Web Tokens). Include the token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Authentication Flow

1. **Register** a new user account
2. **Login** to obtain a JWT token
3. **Include token** in Authorization header for protected endpoints
4. **Refresh token** when it expires (optional)

## API Endpoints

### Health Check

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/health` | Basic health check | None |
| GET | `/health/detailed` | Detailed system health | None |
| GET | `/metrics` | Prometheus-style metrics | None |

### Authentication

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/auth/register` | Register new user | `email`, `password`, `full_name` | User object + token |
| POST | `/auth/login` | Login user | `email`, `password` | User object + token |
| POST | `/auth/logout` | Logout user | None | Success message |
| POST | `/auth/refresh` | Refresh JWT token | `refresh_token` | New access token |
| POST | `/auth/forgot-password` | Request password reset | `email` | Success message |
| POST | `/auth/reset-password` | Reset password | `token`, `new_password` | Success message |

### Users

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/users/me` | Get current user profile | Required |
| PUT | `/users/me` | Update user profile | Required |
| DELETE | `/users/me` | Delete user account | Required |
| GET | `/users/{user_id}` | Get user by ID (admin only) | Required (admin) |

### API Keys Management

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/api-keys` | List all API keys | None |
| POST | `/api-keys` | Create new API key | `provider`, `api_key`, `name` |
| GET | `/api-keys/{key_id}` | Get API key by ID | None |
| PUT | `/api-keys/{key_id}` | Update API key | `api_key`, `name`, `is_active` |
| DELETE | `/api-keys/{key_id}` | Delete API key | None |
| POST | `/api-keys/{key_id}/test` | Test API key connectivity | None |

### Documents Management

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/documents` | List all documents | None |
| POST | `/documents` | Upload new document | Multipart form: `file`, `title`, `description` |
| GET | `/documents/{document_id}` | Get document metadata | None |
| DELETE | `/documents/{document_id}` | Delete document | None |
| POST | `/documents/{document_id}/process` | Process document (extract text, chunk, embed) | None |
| GET | `/documents/{document_id}/chunks` | Get document chunks | None |
| GET | `/documents/{document_id}/preview` | Get document preview | None |
| POST | `/documents/{document_id}/reprocess` | Reprocess document with different settings | `chunk_size`, `chunk_overlap`, `chunking_strategy` |

### Chats

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| GET | `/chats` | List all chat sessions | None |
| POST | `/chats` | Create new chat session | `title`, `model`, `use_rag` |
| GET | `/chats/{chat_id}` | Get chat session details | None |
| DELETE | `/chats/{chat_id}` | Delete chat session | None |
| PUT | `/chats/{chat_id}` | Update chat session | `title`, `model`, `use_rag` |
| GET | `/chats/{chat_id}/messages` | Get chat messages | None |
| POST | `/chats/{chat_id}/messages` | Send message to chat | `content`, `use_rag`, `include_sources` |
| DELETE | `/chats/{chat_id}/messages/{message_id}` | Delete message | None |
| POST | `/chats/{chat_id}/stream` | Stream chat response (SSE) | `content`, `use_rag`, `include_sources` |

### Admin (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | System statistics |
| GET | `/admin/users` | List all users |
| PUT | `/admin/users/{user_id}` | Update user (disable/enable, change role) |
| GET | `/admin/documents` | Document audit log |
| GET | `/admin/health` | Detailed system health |
| GET | `/admin/metrics` | Performance metrics |

## Data Models

### User
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-04-15T04:10:33.825Z",
  "updated_at": "2026-04-15T04:10:33.825Z"
}
```

### API Key
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "provider": "openai",
  "name": "OpenAI Production Key",
  "masked_key": "sk-...abc123",
  "is_active": true,
  "last_used_at": "2026-04-15T04:10:33.825Z",
  "created_at": "2026-04-15T04:10:33.825Z"
}
```

### Document
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Project Requirements",
  "description": "Product requirements document",
  "file_name": "prd.pdf",
  "file_size": 1024000,
  "file_type": "application/pdf",
  "status": "processed",
  "chunk_count": 45,
  "processing_time_ms": 1250,
  "created_at": "2026-04-15T04:10:33.825Z",
  "updated_at": "2026-04-15T04:10:33.825Z"
}
```

### Chat Session
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Technical Discussion",
  "model": "gpt-4-turbo",
  "use_rag": true,
  "message_count": 15,
  "created_at": "2026-04-15T04:10:33.825Z",
  "updated_at": "2026-04-15T04:10:33.825Z"
}
```

### Message
```json
{
  "id": "uuid",
  "chat_id": "uuid",
  "role": "user",
  "content": "What is RAG?",
  "tokens": 5,
  "model": "gpt-4-turbo",
  "use_rag": true,
  "sources": [
    {
      "document_id": "uuid",
      "chunk_index": 3,
      "similarity_score": 0.87,
      "content": "Retrieval-Augmented Generation (RAG) combines..."
    }
  ],
  "created_at": "2026-04-15T04:10:33.825Z"
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-04-15T04:10:33.825Z"
}
```

## Rate Limiting

- **Authentication endpoints**: 10 requests per minute per IP
- **API endpoints**: 100 requests per minute per user
- **Document upload**: 5 requests per minute per user
- **Chat endpoints**: 30 requests per minute per user

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## File Upload

### Supported File Types
- PDF (`.pdf`)
- Text (`.txt`)
- Word Document (`.docx`)
- Markdown (`.md`)

### Size Limits
- Maximum file size: 10 MB
- Maximum total storage per user: 100 MB

### Upload Format
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "title=Project Requirements" \
  -F "description=Product requirements document" \
  http://localhost:8000/api/v1/documents
```

## Streaming Responses

Chat endpoints support Server-Sent Events (SSE) for streaming responses:

```javascript
const eventSource = new EventSource('/api/v1/chats/{chat_id}/stream?message=Hello');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content); // Streamed response chunks
};

eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
};
```

## WebSocket Support

Real-time chat updates are available via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chats/{chat_id}');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // Handle incoming messages
};

ws.send(JSON.stringify({
  type: 'message',
  content: 'Hello, world!'
}));
```

## Testing the API

### Using Swagger UI
Navigate to `/docs` when running the backend locally for interactive API documentation and testing.

### Example cURL Commands

1. **Register a new user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'
```

2. **Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

3. **Get user profile:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your_token>"
```

4. **Upload a document:**
```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@/path/to/document.pdf" \
  -F "title=Test Document" \
  -F "description=Test upload"
```

5. **Send a chat message:**
```bash
curl -X POST http://localhost:8000/api/v1/chats/{chat_id}/messages \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is Retrieval-Augmented Generation?",
    "use_rag": true,
    "include_sources": true
  }'
```

## Versioning

The API is versioned using URL path versioning:
- Current version: `v1`
- API endpoints are prefixed with `/api/v1/`

Backward compatibility will be maintained within major versions. Breaking changes will result in a new major version.

## Changelog

### v1.0.0 (2026-04-15)
- Initial release with full RAG functionality
- Authentication and user management
- Document processing pipeline
- Multi-model LLM support
- Real-time chat with streaming
- Admin dashboard endpoints

## Support

For API support:
1. Check the interactive documentation at `/docs`
2. Review this API documentation
3. Contact the development team for issues

---

*Last Updated: 2026-04-15*  
*API Version: v1.0.0*