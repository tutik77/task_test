from fastapi import APIRouter

from app.api.v1.routes import tasks_router

api_router = APIRouter()
api_router.include_router(tasks_router, prefix="/api/v1")

__all__ = ["api_router"]

