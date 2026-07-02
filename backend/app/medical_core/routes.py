from fastapi import APIRouter

from app.medical_core.service import get_medical_summary, medical_core_status

router = APIRouter()


@router.get("/status")
def status():
    return medical_core_status()


@router.get("/summary")
def summary():
    return get_medical_summary()
