from collections.abc import Generator

from app.application.uow import UnitOfWork


def get_uow() -> Generator[UnitOfWork, None, None]:
    with UnitOfWork() as uow:
        yield uow