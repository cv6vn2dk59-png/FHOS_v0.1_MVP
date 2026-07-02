from app.application.uow import UnitOfWork
from app.persistence.system import SystemLog


def test_unit_of_work():
    with UnitOfWork() as uow:
        log = SystemLog(
            level="INFO",
            message="UnitOfWork registry test log",
        )

        uow.repo(SystemLog).add(log)
        uow.commit()

    return {"status": "ok"}