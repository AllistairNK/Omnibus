# Product Requirements Document: AI Chatbot with RAG

## Project Overview
A modern, engaging chatbot with Retrieval-Augmented Generation (RAG) capabilities, featuring a terminal-like interface with ASCII art expressions, microanimations, and rich visuals. The system uses ChromaDB as a vector database, Supabase for regular data storage, FastAPI backend, Angular frontend, and LangChain for RAG implementation.

## Goals
1. Provide an intuitive, beautiful, and engaging user interface with microanimations.
2. Implement RAG to enhance chatbot responses with retrieved context from documents.
3. Allow users to add API keys for third-party AI models (OpenAI, Anthropic, etc.).
4. Display chatbot emotions/expressions via ASCII images in a terminal-like screen.
5. Follow Test-Driven Development (TDD) throughout the project.
6. Ensure scalability and maintainability with modern tech stack.

## Target Audience
- Developers, tech enthusiasts, and users who enjoy retro-terminal aesthetics.
- Organizations needing a customizable chatbot with document retrieval.
- Individuals wanting to experiment with RAG and AI model integrations.

## Features

### Core Features
1. **Chat Interface**
   - Terminal-like screen with monospace font and green/black theme.
   - Real-time streaming of chatbot responses.
   - ASCII art representing chatbot emotions (happy, thinking, confused, etc.).
   - Command-line style input with support for slash commands.

2. **RAG Implementation**
   - Document upload (PDF, TXT, DOCX) via UI.
   - Automatic chunking, embedding, and storage in ChromaDB.
   - Retrieval of relevant context using similarity search.
   - Integration with LangChain for chain construction.

3. **AI Model Management**
   - User can provide API keys for OpenAI, Anthropic, Google Gemini, etc.
   - Model selection dropdown with cost estimates.
   - Secure storage of API keys in Supabase (encrypted).

4. **Chat History & User Management**
   - Persistent chat logs stored in Supabase.
   - User authentication (optional) via Supabase Auth.
   - Ability to revisit past conversations.

5. **Microanimations & Visuals**
   - Smooth transitions, hover effects, and loading animations.
   - Animated ASCII art (e.g., blinking eyes, moving mouth).
   - Particle effects for sent/received messages.
   - Dark/light theme toggle with animated switch.

6. **Admin Panel**
   - Monitor uploaded documents and vector database stats.
   - View usage analytics and token consumption.
   - Manage API keys and model configurations.

### Non-Functional Requirements
- **Performance**: Chat response time < 2 seconds for typical queries.
- **Scalability**: Support up to 10,000 documents per user.
- **Security**: API keys encrypted at rest, HTTPS only.
- **Accessibility**: WCAG 2.1 AA compliant where possible.
- **Cross‑platform**: Responsive design for desktop and tablet.

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.11+
- **Database**: Supabase (PostgreSQL) for relational data (users, chats, documents).
- **Vector DB**: ChromaDB (latest) for embeddings and similarity search.
- **RAG**: LangChain for document loading, splitting, embedding, and retrieval.
- **AI Integration**: LangChain LLM wrappers for OpenAI, Anthropic, etc.
- **Authentication**: JWT tokens via Supabase Auth.
- **API Documentation**: Auto‑generated OpenAPI docs (Swagger UI).

### Frontend (Angular)
- **Framework**: Angular 18+ with TypeScript.
- **UI Library**: Angular Material for base components, custom CSS for terminal theme.
- **Animations**: Angular Animations + GSAP for advanced microanimations.
- **State Management**: NgRx for global state (optional) or Services.
- **HTTP Client**: Angular HttpClient with interceptors for auth.
- **WebSocket**: For real‑time streaming of chatbot responses.

### Infrastructure
- **Hosting**: Backend on Railway/Render; frontend on Vercel/Netlify.
- **CI/CD**: GitHub Actions with test suites.
- **Monitoring**: Logging via Supabase Logs or Sentry.

## Data Models

### Supabase Tables
- `users` (id, email, created_at)
- `api_keys` (id, user_id, provider, encrypted_key, created_at)
- `documents` (id, user_id, filename, file_path, uploaded_at, chunk_count)
- `document_chunks` (id, document_id, chunk_index, content, embedding_id)
- `chats` (id, user_id, title, created_at)
- `messages` (id, chat_id, role, content, timestamp, metadata)

### ChromaDB Collections
- `embeddings_{user_id}`: Stores vector embeddings of document chunks with metadata.

## UI/UX Design

### Terminal Screen
- Black background (#0a0a0a) with green text (#00ff00).
- Fixed‑width font (Courier New, Monaco, etc.).
- ASCII art area (80×25 characters) that updates based on chatbot emotion.
- Input line with blinking cursor.
- Sidebar for document list, model settings, and chat history.

### Microanimations
- **Message send**: Text typing effect with simulated keystrokes.
- **Bot thinking**: Pulsing ASCII spinner (e.g., `[|] [\] [‑] [/]`).
- **Emotion change**: Smooth transition between ASCII faces.
- **Document upload**: Progress bar with ASCII art.
- **Hover effects**: Glow on interactive elements.

### Responsive Layout
- Desktop: Terminal centered with sidebar.
- Tablet: Collapsible sidebar, terminal full width.
- Mobile: Simplified view with focus on chat.

## Test-Driven Development Approach

### Backend Tests
- **Unit Tests**: Pytest for FastAPI routes, services, utilities.
- **Integration Tests**: Test database interactions with test Supabase instance.
- **API Tests**: FastAPI TestClient for endpoint validation.
- **RAG Tests**: Mock ChromaDB and LangChain components.

### Frontend Tests
- **Unit Tests**: Jasmine/Karma for components, services.
- **Integration Tests**: Cypress for end‑to‑end flows.
- **Visual Regression**: Percy for UI consistency.

### CI/CD Pipeline
1. Run linting (black, flake8, prettier, eslint).
2. Execute backend and frontend test suites.
3. Build Docker images (if applicable).
4. Deploy to staging on success.

## Implementation Phases

### Phase 1: Foundation (Week 1‑2)
- Set up monorepo with backend/frontend folders.
- Create FastAPI skeleton with health check.
- Set up Supabase project and define tables.
- Create Angular project with terminal‑style base component.
- Write initial tests for core modules.

### Phase 2: Backend Core (Week 3‑4)
- Implement user authentication (Supabase Auth).
- Build document upload & chunking endpoint.
- Integrate ChromaDB and LangChain for embedding storage.
- Create chat endpoint with basic LLM integration.
- Write comprehensive tests for each endpoint.

### Phase 3: Frontend Core (Week 5‑6)
- Build terminal UI with ASCII art display.
- Implement chat message component with animations.
- Create document upload UI with drag‑and‑drop.
- Integrate with backend APIs.
- Add API key management UI.

### Phase 4: RAG & AI (Week 7‑8)
- Enhance chat endpoint to retrieve context from ChromaDB.
- Support multiple AI model providers.
- Implement streaming responses via WebSocket/SSE.
- Add emotion detection logic to trigger ASCII art changes.

### Phase 5: Polish & Deployment (Week 9‑10)
- Add microanimations across UI.
- Optimize performance (lazy loading, caching).
- Conduct user testing and gather feedback.
- Deploy to production environment.
- Write documentation and user guides.

## Success Metrics
- **User Engagement**: Average session duration > 5 minutes.
- **Accuracy**: RAG improves answer quality (measured by user ratings).
- **Performance**: 95% of chat responses under 2 seconds.
- **Reliability**: 99.9% uptime for core services.

## Risks & Mitigations
- **Risk**: ChromaDB scalability with large document sets.
  - Mitigation: Implement pagination and periodic cleanup of old embeddings.
- **Risk**: API key security.
  - Mitigation: Use Supabase Vault for encryption, never store plaintext.
- **Risk**: Complex animations impacting performance.
  - Mitigation: Use CSS hardware acceleration, debounce events.

## Future Enhancements
1. Voice input/output.
2. Multi‑user collaborative chat rooms.
3. Plugin system for custom commands.
4. Advanced analytics dashboard.
5. Mobile app (React Native/Ionic).

## Appendix

### Tech Stack Details
- **Backend**: FastAPI, SQLAlchemy, LangChain, ChromaDB, Supabase Python Client.
- **Frontend**: Angular 18, RxJS, Angular Animations, GSAP, Tailwind CSS.
- **DevOps**: Docker, GitHub Actions, Supabase CLI.
- **Testing**: Pytest, Cypress, Jasmine, Karma.

### Team Roles
- **Backend Developer**: FastAPI, RAG, database.
- **Frontend Developer**: Angular, animations, UI/UX.
- **DevOps Engineer**: Deployment, CI/CD.
- **QA Engineer**: Test automation, manual testing.

### References
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Angular Animations Guide](https://angular.io/guide/animations)

---

*Document Version: 1.0*  
*Last Updated: 2026‑03‑25*  
*Author: AI Assistant*