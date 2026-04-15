# AI Chatbot with RAG - User Guide

## Overview

Welcome to the AI Chatbot with Retrieval-Augmented Generation (RAG)! This guide will help you get started with using the application to chat with AI, upload documents, and get intelligent responses based on your own documents.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Dashboard Overview](#dashboard-overview)
4. [Chat Interface](#chat-interface)
5. [Document Management](#document-management)
6. [API Key Configuration](#api-key-configuration)
7. [Model Selection](#model-selection)
8. [Slash Commands](#slash-commands)
9. [Settings & Preferences](#settings--preferences)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### Accessing the Application

1. **Open your browser** and navigate to the application URL (e.g., `https://chatbot.yourdomain.com`)
2. **Register** for a new account or **Login** if you already have one

*Screenshot: Landing page with login/register options*

### System Requirements

- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Internet connection
- For document upload: PDF, TXT, DOCX, or MD files (max 10MB)

## Authentication

### Registration

1. Click **"Sign Up"** on the login page
2. Enter your:
   - **Email address**
   - **Full name**
   - **Password** (minimum 8 characters, with uppercase, lowercase, number, and special character)
3. Click **"Create Account"**
4. Check your email for verification (if enabled)

*Screenshot: Registration form*

### Login

1. Enter your **email** and **password**
2. Click **"Sign In"**
3. You'll be redirected to the main dashboard

### Password Recovery

1. Click **"Forgot Password?"** on the login page
2. Enter your **email address**
3. Check your email for password reset instructions
4. Follow the link to create a new password

## Dashboard Overview

After logging in, you'll see the main dashboard with:

1. **Navigation Sidebar** (left)
   - Chat icon - Access chat interface
   - Documents icon - Manage uploaded documents
   - Settings icon - Configure API keys and preferences
   - Admin icon (admin users only) - Access admin dashboard

2. **Main Content Area** (center)
   - Default view shows chat interface
   - ASCII art header with animated bot

3. **Right Sidebar** (optional)
   - Chat history
   - Document list
   - Model information

*Screenshot: Main dashboard layout*

## Chat Interface

### Starting a New Chat

1. Click the **"+"** button in the chat history sidebar or type `/new` in the chat input
2. Enter a **title** for your chat (optional)
3. Select a **model** (GPT-4, Claude, Gemini, etc.)
4. Choose whether to enable **RAG** (Retrieval-Augmented Generation)

### Sending Messages

1. Type your message in the **input box** at the bottom
2. Press **Enter** or click the **send button** (paper plane icon)
3. Watch the bot's response appear in real-time with typing animation

### Chat Features

- **Streaming Responses**: Responses appear word-by-word for a natural conversation feel
- **Source Citations**: When RAG is enabled, sources are shown with confidence scores
- **Message Actions**:
  - Copy message (clipboard icon)
  - Regenerate response (refresh icon)
  - Delete message (trash icon)

*Screenshot: Chat interface with user and bot messages*

### Chat History

- View all previous chats in the **left sidebar**
- Search chats by title or content
- Delete individual chats or clear all history
- Export chat history as JSON or text

## Document Management

### Uploading Documents

1. Click the **"Documents"** icon in the navigation
2. Click **"Upload Document"** button
3. **Drag and drop** files or click to browse
4. Add **title** and **description** (optional)
5. Click **"Upload"**

**Supported formats**: PDF, TXT, DOCX, MD
**Maximum size**: 10MB per file

*Screenshot: Document upload interface*

### Document Processing

After upload, documents are automatically processed:
1. **Text extraction** - Content is extracted from the file
2. **Chunking** - Text is split into manageable chunks
3. **Embedding** - Chunks are converted to vector embeddings
4. **Indexing** - Vectors are stored in the vector database

Processing status is shown with progress indicators:
- ⏳ **Pending** - Waiting to be processed
- 🔄 **Processing** - Currently being processed
- ✅ **Processed** - Ready for RAG queries
- ❌ **Failed** - Error during processing

### Managing Documents

- **View document list** with metadata (type, size, status, chunk count)
- **Preview documents** in a reader view
- **Delete documents** (with confirmation)
- **Reprocess documents** with different chunking settings

### Using Documents in Chat

1. Ensure documents are in **"Processed"** status
2. Start a new chat or use an existing one
3. Enable **RAG** in chat settings
4. Ask questions related to your documents
5. The bot will retrieve relevant information from your documents

*Screenshot: Chat with source citations from documents*

## API Key Configuration

### Adding API Keys

1. Navigate to **Settings > API Keys**
2. Click **"Add API Key"**
3. Select **provider** (OpenAI, Anthropic, Google)
4. Enter your **API key**
5. Give it a **name** for identification
6. Click **"Save"**

**Security Note**: API keys are encrypted and never displayed in full after saving.

### Managing API Keys

- **View all keys** with provider, status, and last used date
- **Test connectivity** to verify keys work
- **Enable/disable** keys without deleting
- **Delete** unused keys

### Provider Support

| Provider | Models | Required for |
|----------|--------|--------------|
| OpenAI | GPT-4, GPT-3.5 | Default chat, embeddings |
| Anthropic | Claude 3 (Opus, Sonnet, Haiku) | Alternative chat |
| Google | Gemini Pro, Gemini Ultra | Alternative chat |

*Screenshot: API key management interface*

## Model Selection

### Choosing a Model

1. In chat settings, click the **model dropdown**
2. Select from available models
3. View **cost estimates** per 1K tokens
4. See **capabilities** comparison

### Model Comparison

| Model | Provider | Best For | Cost/1K tokens |
|-------|----------|----------|----------------|
| GPT-4 Turbo | OpenAI | Complex reasoning, code | $0.01 / $0.03 |
| GPT-3.5 Turbo | OpenAI | General chat, fast responses | $0.0005 / $0.0015 |
| Claude 3 Opus | Anthropic | Long context, analysis | $0.015 / $0.075 |
| Claude 3 Sonnet | Anthropic | Balanced performance | $0.003 / $0.015 |
| Gemini Pro | Google | Multimodal, free tier | $0.000125 / $0.000375 |

### Cost Management

- **Token usage tracking** in settings
- **Cost estimation** before sending messages
- **Usage limits** to prevent unexpected charges
- **Monthly spending reports**

## Slash Commands

The chat interface supports slash commands for quick actions:

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show all available commands | `/help` |
| `/clear` | Clear current chat | `/clear --confirm` |
| `/new` | Start new chat session | `/new "Project Discussion"` |
| `/model` | Switch AI model | `/model gpt-4` |
| `/rag` | Toggle RAG on/off | `/rag on` |
| `/documents` | List uploaded documents | `/documents list` |
| `/upload` | Upload document from URL | `/upload https://example.com/doc.pdf` |
| `/settings` | Open settings panel | `/settings` |
| `/history` | Show chat history | `/history last 10` |
| `/export` | Export chat | `/export json` |
| `/about` | Show app information | `/about` |
| `/exit` | Close current chat | `/exit` |

### Using Commands

1. Type `/` in the chat input
2. See **autocomplete suggestions**
3. Use **Tab** to complete commands
4. Add **arguments** as needed
5. Press **Enter** to execute

*Screenshot: Command autocomplete dropdown*

## Settings & Preferences

### Account Settings

- **Profile information** (name, email)
- **Password change**
- **Account deletion**

### Application Preferences

- **Theme**: Dark/Light mode toggle
- **Animations**: Enable/disable microanimations
- **Notifications**: Browser notification settings
- **Accessibility**: Reduced motion, high contrast

### Chat Settings

- **Default model**: Set preferred AI model
- **Default RAG setting**: Always use RAG or prompt each time
- **Streaming**: Enable/disable real-time streaming
- **Typing speed**: Adjust bot response animation speed

### Privacy & Security

- **Data retention** settings
- **Export data** option
- **Session management** (view active sessions, log out everywhere)

## Advanced Features

### RAG Configuration

Customize how RAG works:

1. **Chunk size**: Adjust text chunk size (default: 1000 characters)
2. **Overlap**: Set chunk overlap percentage (default: 10%)
3. **Similarity threshold**: Minimum score for including sources
4. **Max sources**: Maximum number of sources per response

### Custom Prompts

Create custom system prompts for specific use cases:

1. Navigate to **Settings > Custom Prompts**
2. Click **"Add Prompt"**
3. Enter **name** and **prompt text**
4. Use in chat with `/prompt <name>`

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Focus chat input |
| `Ctrl/Cmd + /` | Show command palette |
| `Ctrl/Cmd + L` | Clear chat |
| `Ctrl/Cmd + N` | New chat |
| `Ctrl/Cmd + H` | Toggle chat history |
| `Ctrl/Cmd + D` | Toggle document sidebar |
| `Ctrl/Cmd + T` | Toggle theme |
| `Ctrl/Cmd + ?` | Show keyboard shortcuts |

## Troubleshooting

### Common Issues

#### "Cannot connect to backend"
- Check your internet connection
- Verify the application URL is correct
- Try refreshing the page

#### "Document processing failed"
- Ensure file is in supported format (PDF, TXT, DOCX, MD)
- Check file size (< 10MB)
- Try re-uploading the document
- Contact support if issue persists

#### "API key not working"
- Verify key is correct and active
- Check provider account for usage limits
- Test key in provider's playground
- Regenerate key if compromised

#### "Slow response times"
- Try a different AI model
- Reduce RAG sources count
- Check network connection
- Contact admin for system status

### Getting Help

1. **In-app help**: Type `/help` in any chat
2. **Documentation**: Visit the documentation site
3. **Support email**: Contact support@yourdomain.com
4. **Community forum**: Join our user community

## Best Practices

### For Effective RAG

1. **Upload relevant documents** - The more relevant your documents, the better the responses
2. **Use descriptive titles** - Helps with document organization and retrieval
3. **Process documents completely** - Wait for "Processed" status before asking related questions
4. **Ask specific questions** - Instead of "Tell me about X", ask "What are the key features of X according to the document?"

### For Cost Management

1. **Use appropriate models** - Use cheaper models for simple queries
2. **Monitor usage** - Check token usage regularly
3. **Set limits** - Configure spending limits in settings
4. **Use RAG efficiently** - RAG can reduce token usage by providing context

### For Privacy

1. **Review documents** - Don't upload sensitive personal information
2. **Use encryption** - For sensitive documents, encrypt before uploading
3. **Regular cleanup** - Delete documents and chats when no longer needed
4. **Check retention policies** - Understand how long data is stored

## Frequently Asked Questions

### Q: Is my data private?
A: Yes, your data is stored in your own Supabase instance and is not shared with other users. API calls to LLM providers may be subject to their privacy policies.

### Q: Can I use my own LLM?
A: Currently, supported providers are OpenAI, Anthropic, and Google. Self-hosted models may be added in future updates.

### Q: How many documents can I upload?
A: The free tier includes 100MB of storage. Premium tiers offer more storage.

### Q: Can I collaborate with others?
A: Currently, the application is single-user. Team features are planned for future releases.

### Q: How do I export my data?
A: Use the export feature in settings to download your chats and documents.

### Q: Is there a mobile app?
A: The web application is responsive and works on mobile browsers. Native apps may be developed in the future.

---

*Last Updated: 2026-04-15*  
*Guide Version: 1.0*

**Need more help?** Type `/help` in the chat or contact our support team.