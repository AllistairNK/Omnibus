"""
API v1 router definition.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, auth, users, api_keys, documents

api_router = APIRouter()

# Include health router
api_router.include_router(health.router, tags=["health"])
# Include auth router
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# Include users router
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Include API keys router
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
# Include documents router
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])