# AI Chatbot with RAG - Production Deployment Guide

## Overview
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
*Deployment Guide Version: 1.0*