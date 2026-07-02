from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id: Any) -> ModelType | None:
        statement = select(self.model).where(self.model.id == id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        statement = select(self.model).offset(skip).limit(limit)
        return list(self.db.execute(statement).scalars().all())

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)