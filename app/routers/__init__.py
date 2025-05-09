from fastapi import APIRouter, Depends

from .auth import router as auth_router
from .user import router as user_router
from .school import router as school_router
from .class_ import router as class_router
from .subject import router as subject_router
from .grade import router as grade_router
from .invitation import router as invitation_router
from .webhook import router as webhook_router
from .ml import router as ml_router
from .statistics import router as statistics_router
from ..auth_dependency import require_auth

# Main API router with authentication
api_router = APIRouter(dependencies=[Depends(require_auth)])

# Public router for unauthenticated endpoints
public_router = APIRouter()

# Include public routers (no auth required)
public_router.include_router(auth_router, prefix="/auth", tags=["auth"])
public_router.include_router(user_router, prefix="/user", tags=["user"])

# Include authenticated routers
api_router.include_router(school_router, prefix="/school", tags=["school"])
api_router.include_router(class_router, prefix="/class", tags=["class"])
api_router.include_router(subject_router, prefix="/subject", tags=["subject"])
api_router.include_router(grade_router, prefix="/grade", tags=["grade"])
api_router.include_router(invitation_router, prefix="/invitation", tags=["invitation"])
api_router.include_router(ml_router, prefix="/ml", tags=["ml"])
api_router.include_router(statistics_router, prefix="/statistics", tags=["statistics"])

__all__ = [
    'api_router',
    'public_router',
    'auth_router',
    'user_router',
    'school_router',
    'class_router',
    'subject_router',
    'grade_router',
    'invitation_router',
    'webhook_router',
    'ml_router',
    'statistics_router'
]
