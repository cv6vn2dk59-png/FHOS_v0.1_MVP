from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.persistence.model_registry  # noqa: F401 — реєструє всі ORM/Repository до першого запиту
from app.api.router import api_router
from app.core.config import get_settings


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description="Family Health Operating System Core Backend",
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.api_prefix,
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "backend": "running",
        "debug": settings.debug,
    }