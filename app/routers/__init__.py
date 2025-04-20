from fastapi import APIRouter, Depends

from app.routers import user, webhook
from app.auth_dependency import require_auth

api_router = APIRouter(dependencies=[Depends(require_auth)])

routers = [
    user.router,
    webhook.router,
]

for router in routers:
    api_router.include_router(router)


__all__ = ["api_router"]
