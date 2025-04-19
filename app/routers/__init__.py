from fastapi import APIRouter

from app.routers import user, webhook

api_router = APIRouter()

routers = [
    user.router,
    webhook.router,
]

for router in routers:
    api_router.include_router(router)


__all__ = ["api_router"]
