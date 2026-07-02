from fastapi import APIRouter

from app.laboratory_engine.service import laboratory_status, supported_lab_formats

router = APIRouter()


@router.get("/status")
def status():
    return laboratory_status()


@router.get("/formats")
def formats():
    return supported_lab_formats()
