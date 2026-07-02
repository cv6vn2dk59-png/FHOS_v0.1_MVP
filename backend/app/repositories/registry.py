from typing import TypeVar

from sqlalchemy.orm import Session

from app.persistence.base import Base
from app.repositories.base import BaseRepository


ModelType = TypeVar("ModelType", bound=Base)


class RepositoryRegistry:
    _repository_classes: dict[type[Base], type[BaseRepository]] = {}

    def __init__(self, db: Session):
        self.db = db
        self._cache: dict[type[Base], BaseRepository] = {}

    @classmethod
    def register(cls, model: type[Base], repository_cls: type[BaseRepository]) -> None:
        """Реєструє спеціалізований Repository-клас для конкретної ORM-моделі.

        Викликається один раз при імпорті модуля (наприклад, у persistence/repository.py
        відповідного модуля). Якщо модель не зареєстрована — repo() повертає generic
        BaseRepository, як і раніше. Profile-модуль нічого не реєструє й лишається
        без змін у поведінці.
        """
        cls._repository_classes[model] = repository_cls

    def repo(self, model: type[ModelType]) -> BaseRepository[ModelType]:
        if model not in self._cache:
            repository_cls = self._repository_classes.get(model, BaseRepository)
            self._cache[model] = repository_cls(self.db, model)

        return self._cache[model]