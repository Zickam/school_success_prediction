from fastapi import APIRouter, Depends

from app.routers import user, webhook, school, class_router

api_router = APIRouter()

routers = [
    user.router,
    webhook.router,
    school.router,
    class_router.router
]

for router in routers:
    api_router.include_router(router)


__all__ = ["api_router"]
