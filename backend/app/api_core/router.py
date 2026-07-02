from fastapi import APIRouter

from app.api_core.routes_system import router as system_router
from app.ai_core.routes import router as ai_router
from app.medical_core.routes import router as medical_router
from app.laboratory_engine.routes import router as laboratory_router
from app.profile_engine.routes import router as profile_router
from app.ai_os.routes import router as ai_os_router
from app.event_api.routes import router as event_router

api_router = APIRouter()

api_router.include_router(system_router, prefix="/system", tags=["System"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Core"])
api_router.include_router(medical_router, prefix="/medical", tags=["Medical Core"])
api_router.include_router(laboratory_router, prefix="/laboratory", tags=["Laboratory Engine"])
api_router.include_router(profile_router, prefix="/profile", tags=["Profile Engine"])
api_router.include_router(ai_os_router, prefix="/ai-os", tags=["AI Operating System"])
api_router.include_router(event_router, prefix="/event", tags=["Universal Event API"])