from fastapi import APIRouter, Depends

from .school import router as school_router
from .user import router as user_router
from .ml import router as ml_router
from ..auth_dependency import require_auth

# Main API router with authentication
api_router = APIRouter(dependencies=[Depends(require_auth)])

# Include all routers
api_router.include_router(school_router)
api_router.include_router(user_router)
api_router.include_router(ml_router)

__all__ = ["api_router"]
