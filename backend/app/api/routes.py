from fastapi import APIRouter

from app.api_core.router import api_router as legacy_api_router


api_router = APIRouter()

api_router.include_router(legacy_api_router)