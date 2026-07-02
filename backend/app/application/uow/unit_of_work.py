from types import TracebackType

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.persistence.base import Base
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class UnitOfWork:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.session: Session | None = None
        self.repositories: RepositoryRegistry | None = None

    def __enter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        self.repositories = RepositoryRegistry(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type:
            self.rollback()
        self.close()

    def repo(self, model: type[Base]) -> BaseRepository:
        if self.repositories is None:
            raise RuntimeError("UnitOfWork repositories are not initialized")
        return self.repositories.repo(model)

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        self.session.rollback()

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
            self.session = None
            self.repositories = None