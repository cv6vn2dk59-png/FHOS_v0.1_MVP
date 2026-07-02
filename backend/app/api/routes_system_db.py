from fastapi import APIRouter, Depends

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.persistence.system import SystemLog


router = APIRouter()


@router.post("/system/db-test")
def create_db_test_log(uow: UnitOfWork = Depends(get_uow)):
    log = SystemLog(
        level="INFO",
        message="FastAPI Dependency Injection DB test",
    )

    created_log = uow.repo(SystemLog).add(log)
    uow.commit()

    return {
        "status": "ok",
        "id": created_log.id,
        "message": created_log.message,
    }