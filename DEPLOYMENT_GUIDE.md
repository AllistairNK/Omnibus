# AI Chatbot with RAG - Deployment Guide

## Overview
This guide provides comprehensive instructions for both local development and production deployment of the AI Chatbot with RAG application.

---

# Local Development Guide

This section covers setting up and running the application locally for development and testing.

## Prerequisites for Local Development

### System Requirements
- **Python 3.11+** with pip
- **Node.js 18+** and npm
- **Docker** (for ChromaDB)
- **Git** for version control

### Accounts & API Keys Required
1. **Supabase Account** - Free tier sufficient for development
2. **OpenAI API Key** - For GPT models and embeddings (required)
3. **Anthropic API Key** - Optional, for Claude models
4. **Google Gemini API Key** - Optional, for Gemini models

## Step 1: Clone and Setup Repository

```bash
# Clone the repository
git clone <repository-url>
cd omnibus
```

## Step 2: Backend Setup

### 2.1 Install Python Dependencies

```bash
cd backend

# Create and activate virtual environment (recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies
pip install --upgrade pip
pip install -e .
```

### 2.2 Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # macOS/Linux
   ```

2. Edit `.env` file with your API keys:

   **Required API Keys:**
   - **Supabase Configuration** (get from Supabase project dashboard):
     - `SUPABASE_URL`: Your Supabase project URL
     - `SUPABASE_KEY`: Your anon/public key
     - `SUPABASE_JWT_SECRET`: JWT secret from API settings
     - `DATABASE_URL`: PostgreSQL connection string from Supabase

   - **OpenAI API** (required for embeddings and chat):
     - `OPENAI_API_KEY`: Your OpenAI API key (starts with `sk-`)

   **Optional API Keys:**
   - `ANTHROPIC_API_KEY`: For Claude models
   - `GEMINI_API_KEY`: For Google Gemini models

   **Local Development Settings:**
   ```env
   ENVIRONMENT=development
   DEBUG=true
   CHROMA_HOST=localhost
   CHROMA_PORT=8000
   BACKEND_CORS_ORIGINS=http://localhost:4200,http://localhost:3000
   SECRET_KEY=development-secret-key-change-in-production
   ```

### 2.3 Start ChromaDB with Docker

```bash
# Start ChromaDB vector database
docker-compose up -d chromadb

# Verify ChromaDB is running
docker ps | findstr chromadb  # Windows
# or
docker ps | grep chromadb     # macOS/Linux
```

### 2.4 Run Database Migrations

```bash
# Apply database schema
python migrations/run_migrations.py
```

### 2.5 Start Backend Server

```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

The backend will be available at: `http://localhost:8000`

**Verify Backend is Running:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"AI Chatbot Backend",...}
```

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Step 3: Frontend Setup

### 3.1 Install Node.js Dependencies

```bash
cd frontend
npm install
```

### 3.2 Configure Frontend Proxy

The frontend uses relative URLs (`/api/v1/*`) which need to be proxied to the backend. Create a proxy configuration file:

**Create `frontend/proxy.conf.json`:**
```json
{
  "/api": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true
  }
}
```

**Update `angular.json`** to use the proxy configuration:
Add the proxy config to the serve options:
```json
"serve": {
  "builder": "@angular-devkit/build-angular:dev-server",
  "options": {
    "proxyConfig": "proxy.conf.json"
  },
  "configurations": {
    "production": {
      "buildTarget": "ai-chatbot-frontend:build:production"
    },
    "development": {
      "buildTarget": "ai-chatbot-frontend:build:development"
    }
  },
  "defaultConfiguration": "development"
}
```

### 3.3 Start Frontend Development Server

```bash
# Start Angular development server
npm start
# or
ng serve
```

The frontend will be available at: `http://localhost:4200`

## Step 4: Verify Full Stack Integration

1. **Open browser** to `http://localhost:4200`
2. **Test authentication** - Use the bypass login feature or register a new account
3. **Test chat functionality** - Send a message to verify RAG pipeline
4. **Test document upload** - Upload a PDF/TXT document to test document processing

## API Key Management for Local Development

### Where to Get API Keys

1. **Supabase Keys:**
   - Create a free project at [supabase.com](https://supabase.com)
   - Go to Project Settings > API
   - Copy: `SUPABASE_URL`, `SUPABASE_KEY` (anon public key)
   - Go to API Settings > JWT Settings for `SUPABASE_JWT_SECRET`
   - Go to Database > Connection String for `DATABASE_URL`

2. **OpenAI API Key:**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Go to API Keys section
   - Create new secret key
   - Copy to `OPENAI_API_KEY` in `.env`

3. **Anthropic API Key (optional):**
   - Sign up at [console.anthropic.com](https://console.anthropic.com)
   - Create API key
   - Copy to `ANTHROPIC_API_KEY` in `.env`

4. **Google Gemini API Key (optional):**
   - Go to [makersuite.google.com](https://makersuite.google.com)
   - Get API key from Google AI Studio
   - Copy to `GEMINI_API_KEY` in `.env`

### Security Best Practices for Local Development

- **Never commit `.env` files** to version control
- Use `.gitignore` to exclude sensitive files
- For team development, share `.env.example` without actual keys
- Consider using password managers or secure vaults for sharing keys

## Running Tests

### Backend Tests
```bash
cd backend
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test module
pytest tests/test_auth.py -v
```

### Frontend Tests
```bash
cd frontend
# Unit tests
npm test

# Linting
npm run lint

# Formatting check
npm run format:check
```

## Troubleshooting Common Local Issues

### 1. ChromaDB Connection Issues
```
Error: Cannot connect to ChromaDB at localhost:8000
```
**Solution:**
- Ensure Docker is running: `docker ps`
- Start ChromaDB: `docker-compose up -d chromadb`
- Wait 30 seconds for ChromaDB to initialize
- Test connection: `curl http://localhost:8000/api/v1/heartbeat`

### 2. Database Connection Errors
```
asyncpg.exceptions.PostgresConnectionError: connection failed
```
**Solution:**
- Verify `DATABASE_URL` in `.env` is correct
- Check Supabase project is active
- Ensure IP is allowed in Supabase network settings

### 3. CORS Errors in Browser
```
Access to fetch at 'http://localhost:8000/api/v1/auth/login' from origin 'http://localhost:4200' has been blocked by CORS policy
```
**Solution:**
- Ensure `BACKEND_CORS_ORIGINS` includes `http://localhost:4200`
- Restart backend after changing `.env`
- Check proxy configuration in frontend

### 4. Missing API Keys
```
OPENAI_API_KEY is required but not set
```
**Solution:**
- Verify `.env` file exists in `backend/` directory
- Check variable names match `.env.example`
- Restart backend after updating `.env`

### 5. Frontend Can't Connect to Backend
```
Failed to load resource: the server responded with a status of 404 (Not Found)
```
**Solution:**
- Ensure backend is running on port 8000
- Verify proxy configuration
- Check browser developer tools Network tab
- Try direct API call: `curl http://localhost:8000/api/v1/health`

### 6. Python Dependency Issues
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:**
- Activate virtual environment: `venv\Scripts\activate` (Windows)
- Reinstall dependencies: `pip install -e .`
- Check Python version: `python --version` (should be 3.11+)

## Development Workflow Tips

1. **Start services in order:**
   ```bash
   # Terminal 1: ChromaDB
   docker-compose up -d chromadb
   
   # Terminal 2: Backend
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 3: Frontend
   cd frontend
   npm start
   ```

2. **Monitor logs:**
   - Backend logs: Check terminal running uvicorn
   - Frontend logs: Browser developer console
   - ChromaDB logs: `docker logs ai-chatbot-chromadb`

3. **Use hot reload:**
   - Backend: Auto-reloads on file changes (--reload flag)
   - Frontend: Auto-reloads via Angular CLI

4. **Debug tools:**
   - Backend: Use FastAPI's `/docs` endpoint for API testing
   - Frontend: Use Angular DevTools browser extension
   - Database: Use Supabase dashboard for data inspection

---

# Production Deployment Guide

This guide provides step-by-step instructions for deploying the AI Chatbot with RAG application to production.

## Prerequisites
1. **Supabase Account** - For database and authentication
2. **LLM Provider Accounts** - OpenAI, Anthropic, and/or Google Gemini API keys
3. **Deployment Platforms** - Railway/Render (backend) and Vercel/Netlify (frontend)
4. **Custom Domain** (optional) - For professional branding
5. **SSL Certificate** - Automatically provided by deployment platforms

## Task 10.1: Production Deployment

### 1. Set up Production Supabase Instance

#### Steps:
1. **Create Supabase Project**
   - Go to [Supabase Dashboard](https://app.supabase.com)
   - Click "New Project"
   - Name: `ai-chatbot-production`
   - Database Password: Generate secure password
   - Region: Choose closest to your users
   - Click "Create new project"

2. **Configure Environment Variables**
   - Go to Project Settings > API
   - Copy:
     - `SUPABASE_URL` (Project URL)
     - `SUPABASE_KEY` (anon public key)
     - `SUPABASE_JWT_SECRET` (JWT Secret from API Settings)
   - Go to Database > Connection String
   - Copy `DATABASE_URL` (use pooled connection string)

3. **Run Production Migrations**
   ```bash
   cd backend
   python migrations/run_migrations.py --env production
   ```

### 2. Configure ChromaDB for Production

#### Option A: Managed ChromaDB (Recommended)
1. **Sign up for Chroma Cloud** (if available) or use self-hosted
2. **Configure Environment Variables**:
   ```
   CHROMA_HOST=your-chromadb-host.com
   CHROMA_PORT=8000
   CHROMA_AUTH_TOKEN=your-auth-token
   ```

#### Option B: Self-hosted with Docker
1. **Deploy ChromaDB** using the production docker-compose:
   ```bash
   cd backend
   docker-compose -f docker-compose.prod.yml up -d chromadb
   ```
2. **Set up authentication** (recommended for production):
   ```bash
   docker exec ai-chatbot-chromadb chroma auth create-token --name production-token
   ```

### 3. Deploy Backend to Railway/Render

#### Option A: Railway Deployment
1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Initialize Project**:
   ```bash
   cd backend
   railway init
   ```

3. **Set Environment Variables**:
   ```bash
   railway variables set DATABASE_URL=your-database-url
   railway variables set SUPABASE_URL=your-supabase-url
   # Set all other required variables from .env.example
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

#### Option B: Render Deployment
1. **Create New Web Service** on Render
2. **Connect GitHub repository**
3. **Configure Build Settings**:
   - Build Command: `pip install --no-cache-dir .`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add Environment Variables** from Render dashboard
5. **Deploy**

### 4. Deploy Frontend to Vercel/Netlify

#### Option A: Vercel Deployment
1. **Import Project** on Vercel
2. **Configure Build Settings**:
   - Framework: Angular
   - Build Command: `npm run build`
   - Output Directory: `dist/frontend/browser`
3. **Set Environment Variables**:
   - `NG_APP_API_URL`: Your backend URL
   - `NG_APP_SUPABASE_URL`: Your Supabase URL
   - `NG_APP_SUPABASE_ANON_KEY`: Your Supabase anon key
4. **Deploy**

#### Option B: Netlify Deployment
1. **Import Project** on Netlify
2. **Configure Build Settings**:
   - Build Command: `npm run build`
   - Publish Directory: `dist/frontend/browser`
3. **Set Environment Variables** in Netlify dashboard
4. **Deploy**

### 5. Set up Custom Domain with SSL

#### Steps:
1. **Purchase Domain** (if not already owned)
   - Recommended registrars: Namecheap, Google Domains, Cloudflare

2. **Configure DNS**:
   - Add A record pointing to your deployment platform's IP
   - Add CNAME record for www subdomain

3. **Add Domain to Deployment Platform**:
   - **Vercel/Netlify**: Go to Domain Settings > Add Custom Domain
   - **Railway/Render**: Go to Settings > Domains

4. **SSL Certificate**:
   - Automatically provisioned by deployment platforms
   - Verify domain ownership when prompted

5. **Force HTTPS** (configure in platform settings)

## Environment Variables Checklist

### Backend (Required)
```
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
SECRET_KEY=secure-random-string
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
CHROMA_HOST=your-chromadb-host
CHROMA_PORT=8000
```

### Frontend (Required)
```
NG_APP_API_URL=https://your-backend-domain.com
NG_APP_ENVIRONMENT=production
NG_APP_SUPABASE_URL=https://your-project-ref.supabase.co
NG_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Post-Deployment Verification

1. **Health Check**:
   ```bash
   curl https://your-backend-domain.com/api/v1/health
   ```

2. **API Endpoints Test**:
   - Authentication: `/api/v1/auth/login`
   - Chat: `/api/v1/chats`
   - Documents: `/api/v1/documents`

3. **Frontend Connectivity**:
   - Open frontend URL in browser
   - Test login functionality
   - Test chat with RAG

4. **Monitoring Setup**:
   - Configure error tracking (Sentry)
   - Set up performance monitoring
   - Enable usage analytics

## Troubleshooting

### Common Issues:
1. **CORS Errors**: Ensure `BACKEND_CORS_ORIGINS` includes frontend domain
2. **Database Connection**: Verify `DATABASE_URL` is correct and accessible
3. **ChromaDB Connection**: Check if ChromaDB is running and accessible
4. **API Key Issues**: Verify LLM provider API keys are valid

### Logs Access:
- **Railway**: `railway logs`
- **Render**: Dashboard > Logs
- **Vercel**: Dashboard > Deployments > Select deployment > Logs
- **Netlify**: Dashboard > Deployments > Select deployment > Logs

## Maintenance

### Regular Tasks:
1. **Backup Database**: Supabase provides automatic backups
2. **Update Dependencies**: Regularly update Python and Node.js dependencies
3. **Monitor Costs**: Track LLM API usage and deployment platform costs
4. **Security Updates**: Apply security patches promptly

### Scaling Considerations:
1. **Database**: Upgrade Supabase plan as needed
2. **ChromaDB**: Consider Chroma Cloud for managed scaling
3. **Backend**: Increase resources on Railway/Render
4. **Frontend**: Use CDN caching for static assets

## Support
For deployment issues, refer to:
- [Supabase Documentation](https://supabase.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Netlify Documentation](https://docs.netlify.com)

---

*Last Updated: 2026-03-27*  
*Deployment Guide Version: 2.0*