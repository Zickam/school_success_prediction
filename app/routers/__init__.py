from fastapi import APIRouter
from .user import router as user_router
from .school import router as school_router
from .class_ import router as class_router
from .subject import router as subject_router
from .grade import router as grade_router
from .statistics import router as statistics_router
from .ml import router as ml_router
from .webhook import webhook_router

api_router = APIRouter()

api_router.include_router(user_router, tags=["users"])
api_router.include_router(school_router, tags=["schools"])
api_router.include_router(class_router, tags=["classes"])
api_router.include_router(subject_router, tags=["subjects"])
api_router.include_router(grade_router, tags=["grades"])
api_router.include_router(statistics_router, tags=["statistics"])
api_router.include_router(ml_router, tags=["ml"])

__all__ = [
    "api_router",
    "user_router",
    "school_router",
    "class_router",
    "subject_router",
    "grade_router",
    "statistics_router",
    "ml_router",
    "webhook_router",
]
