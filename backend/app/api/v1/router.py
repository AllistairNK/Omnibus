"""
API v1 router definition.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, auth

api_router = APIRouter()

# Include health router
api_router.include_router(health.router, tags=["health"])
# Include auth router
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])