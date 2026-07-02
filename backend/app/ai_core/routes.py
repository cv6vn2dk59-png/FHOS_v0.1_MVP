from fastapi import APIRouter

from app.ai_core.service import ai_core_status

router = APIRouter()


@router.get("/status")
def status():
    return ai_core_status()
