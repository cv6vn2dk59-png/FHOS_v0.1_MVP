"""
FHOS AI Operating System
Routes
"""

from fastapi import APIRouter

from app.ai_os.service import (
    ai_os_status,
    process_request,
    runtime_test_request,
)

router = APIRouter()


@router.get("/status")
def status():
    return ai_os_status()


@router.get("/demo")
def demo():
    return process_request(
        "Проаналізуй ТТГ після видалення щитоподібної залози"
    )


@router.get("/ask")
def ask(request: str):
    return process_request(request)


@router.get("/runtime-test")
async def runtime_test(provider: str = "auto"):
    return await runtime_test_request(provider)
