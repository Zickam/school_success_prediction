from fastapi import APIRouter

from .classes import router as classes_router
from .schools import router as schools_router
from .subjects import router as subjects_router
from .grades import router as grades_router

router = APIRouter(
    prefix="/schools",
    tags=["schools"]
)

# Include all school-related routers
router.include_router(schools_router)
router.include_router(classes_router)
router.include_router(subjects_router)
router.include_router(grades_router) 