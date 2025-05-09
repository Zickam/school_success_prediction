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
from ..auth_dependency import require_auth

# Main API router with authentication
api_router = APIRouter(dependencies=[Depends(require_auth)])

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(school_router)
api_router.include_router(class_router)
api_router.include_router(subject_router)
api_router.include_router(grade_router)
api_router.include_router(invitation_router)
api_router.include_router(ml_router)

__all__ = [
    'api_router',
    'auth_router',
    'user_router',
    'school_router',
    'class_router',
    'subject_router',
    'grade_router',
    'invitation_router',
    'webhook_router',
    'ml_router'
]
