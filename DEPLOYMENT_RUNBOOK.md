# AI Chatbot with RAG - Deployment Runbook

## Overview

This runbook provides operational procedures for deploying, monitoring, and maintaining the AI Chatbot with RAG application in production. It includes step-by-step deployment instructions, monitoring procedures, troubleshooting guides, and rollback procedures.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Procedures](#deployment-procedures)
3. [Post-Deployment Verification](#post-deployment-verification)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Troubleshooting Procedures](#troubleshooting-procedures)
6. [Rollback Procedures](#rollback-procedures)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Disaster Recovery](#disaster-recovery)
9. [Appendix](#appendix)

## Pre-Deployment Checklist

### Environment Readiness
- [ ] **Production Supabase instance** is configured and accessible
- [ ] **ChromaDB instance** is running and accessible
- [ ] **LLM API keys** are valid and have sufficient quota
- [ ] **Domain names** are configured and DNS propagated
- [ ] **SSL certificates** are provisioned and valid
- [ ] **Backup systems** are in place for databases

### Code Readiness
- [ ] **All tests pass** in CI/CD pipeline
- [ ] **Code review** completed and approved
- [ ] **Version tag** created (e.g., v1.2.3)
- [ ] **Changelog** updated with release notes
- [ ] **Database migrations** tested in staging

### Infrastructure Readiness
- [ ] **Resource quotas** checked (CPU, memory, storage)
- [ ] **Scaling policies** configured
- [ ] **Monitoring tools** configured (Sentry, logging, metrics)
- [ ] **Alerting rules** configured and tested
- [ ] **Backup schedules** verified

## Deployment Procedures

### Deployment Architecture
```
Users → CDN → Frontend (Vercel/Netlify) → Backend (Railway/Render) → Supabase + ChromaDB → LLM APIs
```

### Step 1: Backend Deployment

#### Option A: Railway Deployment
```bash
# 1. Login to Railway CLI
railway login

# 2. Select project
railway link

# 3. Set environment variables
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set DATABASE_URL=postgresql://...
# ... set all other variables from .env.example

# 4. Deploy
railway up
```

#### Option B: Render Deployment
1. **Navigate to Render Dashboard**
2. **Select backend service**
3. **Manual deploy** → **Deploy latest commit**
4. **Monitor deployment logs**

#### Verification
```bash
# Test health endpoint
curl https://api.yourdomain.com/health

# Expected response:
# {"status":"healthy","service":"AI Chatbot Backend","version":"1.2.3"}
```

### Step 2: Frontend Deployment

#### Option A: Vercel Deployment
1. **Navigate to Vercel Dashboard**
2. **Import project** from GitHub
3. **Configure build settings**:
   - Framework: Angular
   - Build Command: `npm run build:production`
   - Output Directory: `dist/frontend/browser`
4. **Set environment variables**:
   - `NG_APP_API_URL`: https://api.yourdomain.com
   - `NG_APP_SUPABASE_URL`: https://your-project.supabase.co
   - `NG_APP_SUPABASE_ANON_KEY`: your-anon-key
5. **Deploy**

#### Option B: Netlify Deployment
1. **Navigate to Netlify Dashboard**
2. **Add new site** → **Import from Git**
3. **Configure build settings**:
   - Build command: `npm run build:production`
   - Publish directory: `dist/frontend/browser`
4. **Set environment variables**
5. **Deploy site**

#### Verification
1. **Visit frontend URL**: https://yourdomain.com
2. **Verify page loads** without errors
3. **Test login functionality**
4. **Check console for errors** (F12 → Console)

### Step 3: Database Migration (if needed)
```bash
# Run production migrations
cd backend
python migrations/run_migrations.py --env production

# Verify migration success
python migrations/run_migrations.py --env production --status
```

### Step 4: ChromaDB Setup (if needed)
```bash
# For self-hosted ChromaDB
cd backend
docker-compose -f docker-compose.prod.yml up -d chromadb

# Verify ChromaDB health
curl http://chromadb.yourdomain.com/api/v1/heartbeat
```

## Post-Deployment Verification

### Smoke Tests
Run the following tests to verify deployment:

1. **Health Check**
   ```bash
   curl https://api.yourdomain.com/health/detailed
   # Should return all components as healthy
   ```

2. **Authentication Test**
   ```bash
   # Register test user
   curl -X POST https://api.yourdomain.com/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'
   
   # Login
   curl -X POST https://api.yourdomain.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!"}'
   ```

3. **API Endpoint Test**
   ```bash
   # Get user profile (with auth token)
   curl -X GET https://api.yourdomain.com/api/v1/users/me \
     -H "Authorization: Bearer <token>"
   ```

4. **Document Upload Test**
   ```bash
   curl -X POST https://api.yourdomain.com/api/v1/documents \
     -H "Authorization: Bearer <token>" \
     -F "file=@test.pdf" \
     -F "title=Test Document"
   ```

5. **Chat Test**
   ```bash
   curl -X POST https://api.yourdomain.com/api/v1/chats \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Chat","model":"gpt-3.5-turbo","use_rag":false}'
   ```

### Performance Tests
1. **Response Time Check**
   ```bash
   time curl -s https://api.yourdomain.com/health > /dev/null
   # Should be < 500ms
   ```

2. **Concurrent Users Test** (optional)
   ```bash
   # Using hey or ab
   hey -n 100 -c 10 https://api.yourdomain.com/health
   ```

### User Acceptance Testing
1. **Manual testing** by QA team
2. **Critical user journeys**:
   - Registration and login
   - Document upload and processing
   - Chat with RAG enabled
   - API key management
3. **Cross-browser testing** (Chrome, Firefox, Safari, Edge)

## Monitoring & Alerting

### Monitoring Dashboard
Access monitoring tools:
- **Sentry**: https://sentry.io (error tracking)
- **Supabase Dashboard**: https://app.supabase.com (database monitoring)
- **Vercel/Netlify Analytics**: Deployment platform dashboards
- **Custom Metrics**: https://api.yourdomain.com/metrics (Prometheus format)

### Key Metrics to Monitor

#### Application Metrics
- **Response time**: P95 < 2s for API endpoints
- **Error rate**: < 1% of requests
- **Request rate**: Requests per minute
- **Active users**: Concurrent users

#### Resource Metrics
- **CPU utilization**: < 80% average
- **Memory usage**: < 90% of allocated
- **Disk space**: > 20% free
- **Network throughput**: Monitor for spikes

#### Business Metrics
- **Documents processed**: Daily count
- **Chat messages**: Messages per hour
- **API key usage**: Token consumption
- **User growth**: New registrations

### Alerting Rules

#### Critical Alerts (PagerDuty/SMS)
- **API down**: Health check fails for 5 minutes
- **Database unavailable**: Connection errors
- **ChromaDB down**: Vector search failures
- **High error rate**: > 5% errors for 10 minutes

#### Warning Alerts (Email/Slack)
- **High latency**: P95 response time > 5s
- **Resource saturation**: CPU > 85% for 15 minutes
- **Approaching limits**: API key quota > 90%
- **Storage warning**: Disk space < 30%

#### Informational Alerts (Slack only)
- **Deployment completed**
- **User milestone reached** (e.g., 1000 users)
- **Scheduled backup completed**

### Daily Health Check
```bash
#!/bin/bash
# Run daily at 9 AM UTC

# 1. Check application health
curl -s https://api.yourdomain.com/health | grep -q '"status":"healthy"'
if [ $? -ne 0 ]; then
  echo "CRITICAL: Application health check failed"
  exit 1
fi

# 2. Check database connectivity
curl -s https://api.yourdomain.com/health/detailed | jq '.database.status' | grep -q 'healthy'
if [ $? -ne 0 ]; then
  echo "WARNING: Database health check failed"
fi

# 3. Check ChromaDB
curl -s https://api.yourdomain.com/health/detailed | jq '.chromadb.status' | grep -q 'healthy'
if [ $? -ne 0 ]; then
  echo "WARNING: ChromaDB health check failed"
fi

# 4. Check disk space (if applicable)
# 5. Check error rates from Sentry
# 6. Send report to Slack
```

## Troubleshooting Procedures

### Issue: Application Not Responding

#### Symptoms
- HTTP 5xx errors
- Timeout errors
- Health check failing

#### Investigation Steps
1. **Check deployment platform status** (Railway/Render status page)
2. **Review application logs**:
   ```bash
   # Railway
   railway logs --tail 100
   
   # Render
   # View logs in Render dashboard
   ```
3. **Check resource utilization** (CPU, memory, disk)
4. **Verify external dependencies**:
   ```bash
   # Test Supabase connection
   curl https://your-project.supabase.co/rest/v1/
   
   # Test ChromaDB
   curl http://chromadb.yourdomain.com/api/v1/heartbeat
   
   # Test OpenAI API (simple test)
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

#### Resolution Steps
1. **Restart application**:
   ```bash
   # Railway
   railway restart
   
   # Render
   # Use "Restart" button in dashboard
   ```
2. **Scale resources** if hitting limits
3. **Check for recent deployments** that might have caused issues
4. **Rollback** if issue started after deployment

### Issue: Database Connection Errors

#### Symptoms
- `asyncpg.exceptions.PostgresConnectionError`
- Database queries timing out
- High latency on database-dependent endpoints

#### Investigation Steps
1. **Check Supabase dashboard** for incidents
2. **Verify connection string** is correct
3. **Check network connectivity**:
   ```bash
   # Test database connection
   psql "$DATABASE_URL" -c "SELECT 1"
   ```
4. **Review database metrics** (connections, queries, locks)

#### Resolution Steps
1. **Restart connection pool** (application restart)
2. **Increase connection limit** in Supabase
3. **Optimize queries** if hitting performance limits
4. **Switch to pooled connection string** if using direct

### Issue: ChromaDB Vector Search Failing

#### Symptoms
- RAG responses not including sources
- `chromadb.errors.ChromaError` in logs
- High latency on chat endpoints with RAG

#### Investigation Steps
1. **Check ChromaDB container status**:
   ```bash
   docker ps | grep chromadb
   docker logs ai-chatbot-chromadb --tail 50
   ```
2. **Test ChromaDB API directly**:
   ```bash
   curl http://chromadb.yourdomain.com/api/v1/collections
   ```
3. **Check disk space** for ChromaDB volume
4. **Verify embeddings are being created** (check document processing logs)

#### Resolution Steps
1. **Restart ChromaDB container**:
   ```bash
   docker-compose -f docker-compose.prod.yml restart chromadb
   ```
2. **Clear and rebuild vector index** if corrupted:
   ```bash
   # Backup first
   docker exec ai-chatbot-chromadb chroma backup /data/backup
   
   # Restart with fresh data
   docker-compose -f docker-compose.prod.yml down -v chromadb
   docker-compose -f docker-compose.prod.yml up -d chromadb
   ```
3. **Increase resources** if hitting memory limits

### Issue: LLM API Rate Limiting

#### Symptoms
- `429 Too Many Requests` errors
- Chat responses failing intermittently
- High latency on chat endpoints

#### Investigation Steps
1. **Check LLM provider status pages**:
   - OpenAI Status: https://status.openai.com
   - Anthropic Status: https://status.anthropic.com
   - Google AI Status: https://status.cloud.google.com
2. **Review API usage metrics**:
   ```bash
   # Check token usage from logs
   grep "tokens_used" backend/logs/app.log | tail -20
   ```
3. **Verify API key quotas** in provider dashboards

#### Resolution Steps
1. **Implement exponential backoff** in retry logic
2. **Rotate API keys** if one is rate-limited
3. **Implement request queuing** for high traffic
4. **Upgrade API tier** if consistently hitting limits

### Issue: File Upload Failures

#### Symptoms
- `413 Request Entity Too Large` errors
- Document processing stuck at "uploading"
- File corruption errors

#### Investigation Steps
1. **Check file size limits** (configured at 10MB)
2. **Verify storage bucket permissions** (Supabase Storage)
3. **Check network connectivity** to Supabase
4. **Review upload logs** for specific errors

#### Resolution Steps
1. **Increase file size limit** if needed (update configuration)
2. **Fix storage bucket permissions** in Supabase dashboard
3. **Implement chunked uploads** for large files
4. **Add client-side validation** for file types and sizes

## Rollback Procedures

### When to Rollback
- Critical bugs affecting core functionality
- Performance degradation > 50%
- Security vulnerabilities introduced
- Data corruption or loss

### Rollback Process

#### Step 1: Decision
- **Product owner** approves rollback
- **Engineering lead** confirms rollback is necessary
- **Communicate** to stakeholders about downtime

#### Step 2: Backend Rollback
```bash
# Railway
railway rollback <deployment-id>

# Render
# Use "Rollback" button in deployment history
```

#### Step 3: Frontend Rollback
- **Vercel**: Use "Promote from previous deployment"
- **Netlify**: Use "Rollback" in Deploys section

#### Step 4: Database Rollback (if needed)
```bash
# Rollback last migration
python migrations/run_migrations.py --env production --rollback

# For data fixes, restore from backup
```

#### Step 5: Verification
1. **Run smoke tests** (same as post-deployment)
2. **Verify core functionality** is restored
3. **Monitor error rates** return to normal
4. **Communicate** rollback completion

### Rollback Communication Template
```
Subject: Emergency Rollback - AI Chatbot vX.Y.Z

We have initiated an emergency rollback from version X.Y.Z to version X.Y.Z-1 due to:

[Brief description of issue]

Expected impact:
- [Duration of downtime]
- [Features affected]
- [Data implications]

The rollback is expected to complete by [time].

We will provide updates as the situation evolves.

Regards,
[Team Name]
```

## Maintenance Procedures

### Weekly Maintenance
1. **Review logs and metrics** for anomalies
2. **Check backup completion** and test restore
3. **Rotate logs** if not automated
4. **Update dependencies** (security patches only)

### Monthly Maintenance
1. **Security audit** of dependencies
2. **Performance review** and optimization
3. **Cost analysis** of LLM API usage
4. **User feedback review** and prioritization

### Quarterly Maintenance
1. **Infrastructure review** and scaling planning
2. **Disaster recovery drill**
3. **Compliance check** (GDPR, SOC2, etc.)
4. **Roadmap alignment** with business goals

### Database Maintenance
```bash
# Weekly: Vacuum and analyze
psql "$DATABASE_URL" -c "VACUUM ANALYZE;"

# Monthly: Reindex
psql "$DATABASE_URL" -c "REINDEX DATABASE your_database;"

# Backup verification (weekly)
# Test restore of latest backup to staging
```

### ChromaDB Maintenance
```bash
# Weekly: Compact database
docker exec ai-chatbot-chromadb chroma compact

# Monthly: Backup
docker exec ai-chatbot-chromadb chroma backup /data/backup/$(date +%Y-%m-%d)

# Quarterly: Reindex if performance degrades
```

## Disaster Recovery

### Recovery Time Objective (RTO)
- **Critical systems**: 1 hour
- **Non-critical systems**: 4 hours

### Recovery Point Objective (RPO)
- **User data**: 15 minutes
- **Chat history**: 1 hour
- **Documents**: 4 hours

### Backup Procedures

#### Database Backups
- **Supabase**: Automated daily backups (retained for 7 days)
- **Manual backup** before major deployments:
  ```bash
  # Export data
  pg_dump "$DATABASE_URL" > backup_$(date +%Y-%m-%d).sql
  
  # Store in secure location (S3, GCS, etc.)
  ```

#### ChromaDB Backups
```bash
# Create backup
docker exec ai-chatbot-chromadb chroma backup /data/backup

# Copy backup to cloud storage
docker cp ai-chatbot-chromadb:/data/backup ./chroma_backup
aws s3 cp ./chroma_backup s3://your-bucket/chroma-backup/$(date +%Y-%m-%d)/
```

#### File Storage Backups
- **Supabase Storage**: Versioning enabled
- **Manual export** of critical documents quarterly

### Recovery Procedures

#### Full Site Recovery
1. **Provision new infrastructure** from IaC templates
2. **Restore database** from latest backup
3. **Restore ChromaDB** from backup
4. **Restore files** from Supabase Storage
5. **Update DNS** to point to new infrastructure
6. **Verify functionality** with smoke tests

#### Partial Recovery Scenarios

##### Database Corruption
1. **Identify last good backup**
2. **Restore to staging** for verification
3. **Schedule maintenance window**
4. **Restore production database**
5. **Replay WAL logs** if available

##### ChromaDB Data Loss
1. **Stop application** to prevent new writes
2. **Restore from latest backup**
3. **Re-process recent documents** if needed
4. **Restart application**

##### LLM API Outage
1. **Switch to alternative provider** (OpenAI → Anthropic)
2. **Implement graceful degradation** (disable RAG, use simpler models)
3. **Communicate service limitations** to users
4. **Monitor provider status** for resolution

## Appendix

### A. Contact Information

#### Technical Contacts
- **Primary On-call**: [Name] - [Phone] - [Slack]
- **Secondary On-call**: [Name] - [Phone] - [Slack]
- **Infrastructure Lead**: [Name] - [Phone] - [Slack]

#### Vendor Contacts
- **Supabase Support**: support@supabase.com
- **OpenAI Support**: https://help.openai.com
- **Railway Support**: https://railway.app/contact
- **Vercel Support**: https://vercel.com/support

### B. Useful Commands

#### Database Commands
```bash
# Check database size
psql "$DATABASE_URL" -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Check active connections
psql "$DATABASE_URL" -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Kill idle connections
psql "$DATABASE_URL" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND pid <> pg_backend_pid();"
```

#### Application Commands
```bash
# View recent errors
grep -i error backend/logs/app.log | tail -20

# Check request rate
tail -1000 backend/logs/app.log | grep "HTTP" | wc -l

# Monitor response times
tail -f backend/logs/app.log | grep "response_time"
```

#### Docker Commands
```bash
# View container logs
docker logs ai-chatbot-chromadb --tail 50 -f

# Check container resources
docker stats ai-chatbot-chromadb

# Restart container
docker-compose -f docker-compose.prod.yml restart chromadb
```

### C. Configuration Files

#### Environment Variables Checklist
```bash
# Backend (required)
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=sk-...
SECRET_KEY=secure-random-string
BACKEND_CORS_ORIGINS=https://yourdomain.com
CHROMA_HOST=chromadb.yourdomain.com
CHROMA_PORT=8000

# Frontend (required)
NG_APP_API_URL=https://api.yourdomain.com
NG_APP_SUPABASE_URL=https://your-project.supabase.co
NG_APP_SUPABASE_ANON_KEY=your-anon-key
```

### D. Glossary

- **RTO**: Recovery Time Objective - Maximum acceptable downtime
- **RPO**: Recovery Point Objective - Maximum acceptable data loss
- **LLM**: Large Language Model (GPT, Claude, Gemini)
- **RAG**: Retrieval-Augmented Generation
- **SSE**: Server-Sent Events (for streaming)
- **JWT**: JSON Web Token (for authentication)

### E. Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-04-15 | 1.0.0 | Initial runbook | [Your Name] |
| 2026-04-20 | 1.1.0 | Added troubleshooting procedures | [Name] |

---

*Last Updated: 2026-04-15*  
*Runbook Version: 1.0.0*

**Important**: This runbook should be reviewed and updated quarterly or after any significant infrastructure changes.