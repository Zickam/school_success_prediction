from fastapi import APIRouter
from .user import router as user_router
from .school import router as school_router
from .class_ import router as class_router
from .subject import router as subject_router
from .grade import router as grade_router
from .statistics import router as statistics_router
from .webhook import webhook_router

api_router = APIRouter()

# Include all routers
api_router.include_router(user_router, prefix="/user", tags=["user"])
api_router.include_router(school_router, prefix="/school", tags=["school"])
api_router.include_router(class_router, prefix="/class", tags=["class"])
api_router.include_router(subject_router, prefix="/subject", tags=["subject"])
api_router.include_router(grade_router, prefix="/grade", tags=["grade"])
api_router.include_router(statistics_router, prefix="/statistics", tags=["statistics"])

__all__ = [
    'api_router',
    'user_router',
    'school_router',
    'class_router',
    'subject_router',
    'grade_router',
    'statistics_router',
    'webhook_router',
]
