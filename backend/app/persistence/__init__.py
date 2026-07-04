"""Мінімальний персистентний інфраструктурний шар.

Містить лише SQLAlchemy Base. НЕ імпортує конкретні ORM-моделі — це
навмисно, щоб уникнути циклічного імпорту: кожен ORM-файл сам імпортує
Base з цього пакету, а якби цей файл одразу імпортував той самий ORM-файл
через `from X import Клас`, виникає цикл, що ламається, коли ORM-файл
імпортується напряму як перший імпорт у процесі (сталось з ReferenceRangeORM).

Реєстрація ORM-моделей для Alembic autogenerate та RepositoryRegistry
винесена в app/persistence/model_registry.py.
"""

from app.persistence.base import Base

__all__ = ["Base"]