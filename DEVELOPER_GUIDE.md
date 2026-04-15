# AI Chatbot with RAG - Developer Setup Guide

## Overview

This guide provides comprehensive instructions for developers to set up the development environment, understand the codebase structure, and contribute to the AI Chatbot with RAG project.

## Prerequisites

### System Requirements
- **Python 3.11+** with pip
- **Node.js 18+** and npm
- **Docker** and Docker Compose (for ChromaDB)
- **Git** for version control
- **VS Code** (recommended) or any IDE

### Accounts Required
1. **Supabase Account** (free tier) - For database and authentication
2. **OpenAI API Key** - For GPT models and embeddings
3. **GitHub Account** - For repository access

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd omnibus
```

### 2. One-Command Setup (Optional)
```bash
# Run the setup script (if available)
./scripts/setup-dev.sh
```

## Project Structure

```
omnibus/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core utilities (config, auth, database)
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   ├── tests/              # Backend tests
│   ├── migrations/         # Database migrations
│   ├── pyproject.toml      # Python dependencies
│   └── docker-compose.yml  # Docker configuration
├── frontend/               # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/       # Core services, guards, interceptors
│   │   │   ├── modules/    # Feature modules
│   │   │   └── state/      # NgRx state management
│   │   └── styles.scss     # Global styles
│   ├── package.json        # Node.js dependencies
│   └── angular.json        # Angular configuration
├── docs/                   # Documentation
└── scripts/                # Development scripts
```

## Backend Development Setup

### 1. Python Environment Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .[dev]  # Includes development dependencies
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY
```

### 3. Database Setup
```bash
# Start ChromaDB (vector database)
docker-compose up -d chromadb

# Run database migrations
python migrations/run_migrations.py

# Seed sample data (optional)
python migrations/run_migrations.py --seed
```

### 4. Start Backend Server
```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Use the provided script
python scripts/run_dev.py
```

**Verify Backend:** Visit `http://localhost:8000/docs` for Swagger UI.

## Frontend Development Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Proxy
Ensure `frontend/proxy.conf.json` exists and points to backend:
```json
{
  "/api": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true
  }
}
```

### 3. Start Development Server
```bash
npm start
# or
ng serve
```

**Verify Frontend:** Visit `http://localhost:4200`

## Development Workflow

### Running Tests

#### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run tests with markers
pytest -m "not slow"
```

#### Frontend Tests
```bash
cd frontend

# Unit tests
npm test

# E2E tests (if configured)
npm run e2e

# Linting
npm run lint

# Formatting check
npm run format:check
```

### Code Quality Tools

#### Backend
- **Black**: Code formatting
  ```bash
  black app/ tests/
  ```
- **isort**: Import sorting
  ```bash
  isort app/ tests/
  ```
- **Flake8**: Linting
  ```bash
  flake8 app/ tests/
  ```
- **Mypy**: Type checking
  ```bash
  mypy app/
  ```

#### Frontend
- **Prettier**: Code formatting
  ```bash
  npm run format
  ```
- **ESLint**: Linting
  ```bash
  npm run lint
  ```
- **TypeScript**: Type checking
  ```bash
  npx tsc --noEmit
  ```

### Git Hooks
Pre-commit hooks are configured to run:
- Code formatting (Black, Prettier)
- Linting (Flake8, ESLint)
- Type checking (Mypy, TypeScript)
- Test suite (pytest)

To bypass hooks (when necessary):
```bash
git commit --no-verify
```

## Architecture Overview

### Backend Architecture
```
Request → FastAPI Middleware → Authentication → Router → Service → Database/External API → Response
```

**Key Components:**
1. **FastAPI**: Web framework with automatic OpenAPI documentation
2. **Supabase**: PostgreSQL database and authentication
3. **ChromaDB**: Vector database for embeddings
4. **LangChain**: RAG pipeline orchestration
5. **Pydantic**: Data validation and settings management

### Frontend Architecture
```
Angular App → NgRx Store → Services → Components → Backend API
```

**Key Components:**
1. **Angular 18**: Framework with TypeScript
2. **NgRx**: State management (RxJS-based)
3. **Angular Material**: UI component library
4. **RxJS**: Reactive programming library
5. **SCSS**: Styling with CSS preprocessor

## Adding New Features

### 1. Backend Feature Development

#### Create a New API Endpoint
1. **Create service** in `app/services/`
2. **Create endpoint** in `app/api/v1/endpoints/`
3. **Add to router** in `app/api/v1/router.py`
4. **Write tests** in `tests/`
5. **Update OpenAPI documentation** with docstrings

Example endpoint structure:
```python
@router.post("/new-feature", response_model=FeatureResponse)
async def create_feature(
    request: FeatureRequest,
    current_user: User = Depends(get_current_user),
) -> FeatureResponse:
    """
    Create a new feature.
    
    Args:
        request: Feature request data
        current_user: Authenticated user
        
    Returns:
        Feature response with created data
    """
    feature = await feature_service.create_feature(
        user_id=current_user.id,
        data=request
    )
    return FeatureResponse.from_orm(feature)
```

#### Create a New Service
```python
# app/services/new_service.py
class NewService:
    def __init__(self, db: Database):
        self.db = db
    
    async def perform_action(self, data: dict) -> Result:
        # Business logic here
        pass
```

### 2. Frontend Feature Development

#### Create a New Component
```bash
# Generate component
ng generate component modules/feature/components/new-feature

# Generate service
ng generate service core/services/feature
```

#### Component Structure
```typescript
@Component({
  selector: 'app-new-feature',
  templateUrl: './new-feature.component.html',
  styleUrls: ['./new-feature.component.scss']
})
export class NewFeatureComponent implements OnInit {
  constructor(private featureService: FeatureService) {}
  
  ngOnInit(): void {
    // Initialization logic
  }
}
```

#### Add to NgRx Store (if needed)
1. **Create actions** in `app/core/state/feature/`
2. **Create reducer** to handle state changes
3. **Create effects** for side effects
4. **Create selectors** for data retrieval

## Database Management

### Migrations
```bash
# Create new migration
python migrations/create_migration.py "add_new_table"

# Run migrations
python migrations/run_migrations.py

# Rollback last migration
python migrations/run_migrations.py --rollback
```

### Schema Changes
1. Update SQL in `migrations/` directory
2. Update Pydantic models in `app/models/`
3. Update database service in `app/core/database.py`
4. Run migration and update tests

## Environment Configuration

### Backend Environment Variables
```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-...

# Optional
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# Development
ENVIRONMENT=development
DEBUG=true
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

### Frontend Environment Variables
Create `frontend/src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  supabaseUrl: 'https://your-project.supabase.co',
  supabaseAnonKey: 'your-anon-key'
};
```

## Testing Strategy

### Backend Testing
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints with database
- **Performance Tests**: Benchmark critical paths
- **Mock External Services**: Use `tests/mocks.py`

### Frontend Testing
- **Component Tests**: Test UI components with TestBed
- **Service Tests**: Test business logic services
- **E2E Tests**: Test user workflows (if configured)

### Test Data
Use factory functions from `tests/factories.py`:
```python
user = UserFactory.create()
document = DocumentFactory.create(user_id=user.id)
```

## Debugging

### Backend Debugging
```bash
# Run with debugger
python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload

# VS Code launch configuration
# Add to .vscode/launch.json:
{
  "name": "Python: FastAPI",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  }
}
```

### Frontend Debugging
- **Browser DevTools**: Console, Network, Sources tabs
- **Angular DevTools**: Browser extension for Angular debugging
- **Redux DevTools**: For NgRx state inspection

### Common Debugging Scenarios
1. **CORS Issues**: Check `BACKEND_CORS_ORIGINS` includes frontend URL
2. **Database Connection**: Verify Supabase credentials and network access
3. **ChromaDB Issues**: Ensure Docker container is running
4. **API Key Errors**: Check environment variables are set correctly

## Performance Optimization

### Backend Optimization
- **Database Indexing**: Add indexes for frequently queried columns
- **Query Optimization**: Use `EXPLAIN ANALYZE` for slow queries
- **Caching**: Implement Redis for frequent queries
- **Connection Pooling**: Configure asyncpg connection pool

### Frontend Optimization
- **Lazy Loading**: Split code with Angular lazy loading
- **Virtual Scrolling**: For long lists
- **Change Detection**: Use `OnPush` strategy where possible
- **Bundle Optimization**: Analyze bundle with `webpack-bundle-analyzer`

## Security Considerations

### Backend Security
- **Input Validation**: Use Pydantic models for all inputs
- **Authentication**: JWT validation with Supabase
- **Authorization**: Role-based access control
- **API Key Encryption**: Encrypt API keys at rest
- **SQL Injection Prevention**: Use parameterized queries

### Frontend Security
- **XSS Protection**: Angular's built-in sanitization
- **CSRF Protection**: Use anti-CSRF tokens
- **Content Security Policy**: Configure CSP headers
- **Secure Storage**: Don't store sensitive data in localStorage

## Monitoring and Logging

### Backend Logging
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("User logged in", extra={"user_id": user.id})
logger.error("Database connection failed", exc_info=True)
```

### Frontend Logging
```typescript
import { Logger } from '@app/core/services/logger.service';

constructor(private logger: Logger) {}

this.logger.info('Component initialized');
this.logger.error('API call failed', error);
```

### Monitoring Endpoints
- `/health`: Basic health check
- `/health/detailed`: Detailed system health
- `/metrics`: Prometheus metrics
- `/api/v1/admin/health`: Admin health dashboard

## Deployment Preparation

### Before Deployment Checklist
1. [ ] All tests pass
2. [ ] Code linting passes
3. [ ] Type checking passes
4. [ ] Documentation updated
5. [ ] Environment variables configured
6. [ ] Database migrations tested
7. [ ] Performance benchmarks met

### Build for Production
```bash
# Backend
cd backend
pip install --no-cache-dir .

# Frontend
cd frontend
npm run build:production
```

## Contributing Guidelines

### Code Style
- Follow PEP 8 for Python
- Follow Angular Style Guide for TypeScript
- Use meaningful variable and function names
- Add docstrings for all public functions and classes

### Commit Messages
Use conventional commits format:
```
feat: add new document processing endpoint
fix: resolve CORS issue in development
docs: update API documentation
test: add unit tests for auth service
chore: update dependencies
```

### Pull Request Process
1. **Create feature branch** from `develop`
2. **Implement changes** with tests
3. **Run all tests** and ensure they pass
4. **Update documentation** as needed
5. **Create PR** with description of changes
6. **Address review comments**
7. **Merge after approval**

### Review Checklist
- [ ] Code follows project conventions
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered

## Troubleshooting Development Issues

### Common Issues and Solutions

#### "ModuleNotFoundError" in Python
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate

# Reinstall dependencies
pip install -e .
```

#### "Cannot connect to ChromaDB"
```bash
# Check Docker is running
docker ps

# Start ChromaDB
docker-compose up -d chromadb

# Wait for initialization
sleep 10
```

#### "CORS errors" in browser
```bash
# Ensure BACKEND_CORS_ORIGINS includes frontend URL
# In .env:
BACKEND_CORS_ORIGINS=http://localhost:4200,http://localhost:3000

# Restart backend after changing .env
```

#### "Angular build errors"
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check TypeScript version compatibility
npx tsc --version
```

#### "Database migration failures"
```bash
# Check Supabase connection
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('your-database-url'))"

# Run migrations with verbose output
python migrations/run_migrations.py --verbose
```

## Getting Help

### Internal Resources
- **API Documentation**: `API_DOCUMENTATION.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **User Guide**: `USER_GUIDE.md`
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md`

### External Resources
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Angular Documentation**: https://angular.io/docs
- **Supabase Documentation**: https://supabase.com/docs
- **ChromaDB Documentation**: https://docs.trychroma.com

### Support Channels
- **GitHub Issues**: For bug reports and feature requests
- **Team Slack/Teams**: For internal discussions
- **Code Reviews**: For implementation guidance

## Next Steps for Developers

1. **Explore the codebase**: Start with `backend/app/main.py` and `frontend/src/app/app.component.ts`
2. **Run the application**: Follow the setup instructions above
3. **Make a small change**: Fix a typo or add a test to get familiar
4. **Pick an issue**: Check GitHub issues for beginner-friendly tasks
5. **Join discussions**: Participate in design and architecture discussions

---

*Last Updated: 2026-04-15*  
*Guide Version: 1.0*

**Happy coding!** 🚀