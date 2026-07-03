from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
MODULES_DIR = APP_DIR / "modules"
TESTS_DIR = BASE_DIR / "tests" / "modules"
PERSISTENCE_INIT = APP_DIR / "persistence" / "__init__.py"
API_ROUTER = APP_DIR / "api" / "router.py"


TEMPLATE_FILES = {
    "__init__.py": "",

    "api/__init__.py": "",

    "api/routes.py": '''from fastapi import APIRouter, Depends, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.{module_name}.application.service import {class_name}Service
from app.modules.{module_name}.schemas.{module_name} import (
    {class_name}Create,
    {class_name}Read,
)


router = APIRouter(prefix="/{route_prefix}", tags=["{module_title}"])


@router.post("/", response_model={class_name}Read, status_code=status.HTTP_201_CREATED)
def create_{module_name}(
    data: {class_name}Create,
    uow: UnitOfWork = Depends(get_uow),
):
    service = {class_name}Service(uow)
    return service.create(data)


@router.get("/", response_model=list[{class_name}Read])
def list_{module_name}(
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
):
    service = {class_name}Service(uow)
    return service.list(skip=skip, limit=limit)
''',

    "application/__init__.py": "",

    "application/service.py": '''from app.application.uow import UnitOfWork
from app.modules.{module_name}.domain.entities import {class_name}
from app.modules.{module_name}.persistence import mapper
from app.modules.{module_name}.persistence.orm import {class_name}ORM
from app.modules.{module_name}.schemas.{module_name} import {class_name}Create


class {class_name}Service:
    """Стартовий Application Service. Domain ({class_name}) наразі містить лише
    базові поля — клінічну/бізнес-логіку (методи на кшталт interpret(),
    is_out_of_range(), risk_score()) потрібно додати в domain/entities.py
    за прикладом app/modules/laboratory/domain/entities.py, ПЕРЕД тим як
    цей модуль вважати production-ready.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create(self, data: {class_name}Create) -> {class_name}:
        domain_obj = {class_name}()

        orm_obj = mapper.to_orm(domain_obj)
        self.uow.repo({class_name}ORM).add(orm_obj)
        self.uow.commit()

        return mapper.to_domain(orm_obj)

    def list(self, skip: int = 0, limit: int = 100) -> list[{class_name}]:
        orm_objects = self.uow.repo({class_name}ORM).list(skip=skip, limit=limit)
        return [mapper.to_domain(obj) for obj in orm_objects]
''',

    "domain/__init__.py": "",

    "domain/entities.py": '''from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class {class_name}:
    """Domain-модель {module_title}.

    Constitution (розділ DOMAIN): Domain не може бути Anemic Model.
    Цей клас — лише структурний каркас (id, created_at, updated_at).
    Перед тим як вважати модуль production-ready, сюди потрібно додати
    реальні методи бізнес-логіки (правила, інваріанти, розрахунки,
    клінічну логіку, валідацію) — за прикладом
    app/modules/laboratory/domain/entities.py::LaboratoryResult.
    """

    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
''',

    "persistence/__init__.py": "",

    "persistence/orm.py": '''from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class {class_name}ORM(Base):
    __tablename__ = "{table_name}"

    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
''',

    "persistence/mapper.py": '''from app.modules.{module_name}.domain.entities import {class_name}
from app.modules.{module_name}.persistence.orm import {class_name}ORM


def to_domain(orm: {class_name}ORM) -> {class_name}:
    return {class_name}(
        id=orm.id,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def to_orm(domain: {class_name}) -> {class_name}ORM:
    return {class_name}ORM()
''',

    "persistence/repository.py": '''from app.modules.{module_name}.persistence.orm import {class_name}ORM
from app.repositories.base import BaseRepository
from app.repositories.registry import RepositoryRegistry


class {class_name}Repository(BaseRepository[{class_name}ORM]):
    """Додай сюди спеціалізовані query-методи за потребою
    (за прикладом LaboratoryRepository.get_results_for_patient),
    коли Domain-модель отримає поля, за якими треба фільтрувати/сортувати.
    """
    pass


RepositoryRegistry.register({class_name}ORM, {class_name}Repository)
''',

    "schemas/__init__.py": "",

    "schemas/{module_name}.py": '''from datetime import datetime

from pydantic import BaseModel, ConfigDict


class {class_name}Create(BaseModel):
    pass


class {class_name}Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
''',
}

TEST_TEMPLATE = '''from app.modules.{module_name}.domain.entities import {class_name}


def test_{module_name}_instantiates():
    """Мінімальний smoke-тест: підтверджує, що Domain-модель імпортується
    і створюється. Замінити/доповнити реальними тестами клінічної логіки,
    коли domain/entities.py отримає бізнес-методи (Constitution: кожна
    бізнес-логіка повинна мати автоматизовані тести).
    """
    instance = {class_name}()
    assert instance.id is None
'''


def to_class_name(module_name: str) -> str:
    return "".join(part.capitalize() for part in module_name.split("_"))


def _register_in_persistence_init(module_name: str, class_name: str) -> None:
    """Дописує імпорти ORM і Repository в app/persistence/__init__.py.

    Без цього кроку RepositoryRegistry.register(...) і Base.metadata
    ніколи не побачать новий модуль (та сама причина Знахідок 6/7/12
    зі Sprint 3 Laboratory) — Alembic autogenerate згенерує порожню
    міграцію, а uow.repo(...) мовчки поверне generic BaseRepository.
    """
    content = PERSISTENCE_INIT.read_text(encoding="utf-8")

    orm_import = (
        f"from app.modules.{module_name}.persistence.orm import {class_name}ORM"
    )
    repo_import = (
        f"from app.modules.{module_name}.persistence.repository import "
        f"{class_name}Repository  # noqa: F401 — реєструє в RepositoryRegistry"
    )

    if orm_import in content:
        print(f"SKIP: {PERSISTENCE_INIT} вже містить імпорт {class_name}ORM")
        return

    lines = content.splitlines()
    insert_at = next(
        (i for i, line in enumerate(lines) if line.strip().startswith("__all__")),
        len(lines),
    )

    lines.insert(insert_at, orm_import)
    lines.insert(insert_at + 1, repo_import)
    lines.insert(insert_at + 2, "")

    new_content = "\n".join(lines)

    if "__all__" in new_content:
        new_content = new_content.replace(
            '__all__ = [',
            f'__all__ = [\n    "{class_name}ORM",\n    "{class_name}Repository",',
            1,
        )

    PERSISTENCE_INIT.write_text(new_content, encoding="utf-8")
    print(f"OK: {PERSISTENCE_INIT} оновлено (додано {class_name}ORM, {class_name}Repository)")


def _register_router(module_name: str, route_prefix: str) -> None:
    """Дописує імпорт і include_router() в app/api/router.py.

    Без цього роут існує в коді, але недосяжний по HTTP (Знахідка 12
    зі Sprint 3 Laboratory — модуль був повністю готовий, але не
    зареєстрований, і всі запити повертали 404).
    """
    content = API_ROUTER.read_text(encoding="utf-8")

    router_import = (
        f"from app.modules.{module_name}.api.routes import router as {module_name}_router"
    )
    include_line = f"api_router.include_router({module_name}_router)"

    if router_import in content:
        print(f"SKIP: {API_ROUTER} вже містить імпорт {module_name}_router")
        return

    lines = content.splitlines()

    last_import_idx = max(
        i for i, line in enumerate(lines) if line.strip().startswith(("from ", "import "))
    )
    lines.insert(last_import_idx + 1, router_import)

    legacy_idx = next(
        (i for i, line in enumerate(lines) if "legacy_api_router" in line and "include_router" in line),
        None,
    )
    insert_at = legacy_idx if legacy_idx is not None else len(lines)
    lines.insert(insert_at, include_line)

    API_ROUTER.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: {API_ROUTER} оновлено (роут /{route_prefix} підключений)")


def create_module(module_name: str) -> None:
    module_name = module_name.strip().lower().replace("-", "_")
    class_name = to_class_name(module_name)
    module_title = class_name
    route_prefix = module_name.replace("_", "-")
    table_name = module_name + "s"

    module_dir = MODULES_DIR / module_name
    if module_dir.exists():
        print(f"ERROR: Module already exists: {module_dir}")
        return

    for relative_path, template in TEMPLATE_FILES.items():
        relative_path = relative_path.format(module_name=module_name)
        file_path = module_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = template.format(
            module_name=module_name,
            class_name=class_name,
            module_title=module_title,
            route_prefix=route_prefix,
            table_name=table_name,
        )
        file_path.write_text(content, encoding="utf-8")

    test_dir = TESTS_DIR / module_name
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "__init__.py").write_text("", encoding="utf-8")
    (test_dir / f"test_{module_name}_domain.py").write_text(
        TEST_TEMPLATE.format(module_name=module_name, class_name=class_name),
        encoding="utf-8",
    )

    _register_in_persistence_init(module_name, class_name)
    _register_router(module_name, route_prefix)

    print(f"OK: module created: app/modules/{module_name}")
    print(f"OK: tests created: tests/modules/{module_name}")
    print()
    print("Наступні кроки (ручні, бо потребують доменного рішення):")
    print(f"1. Додай реальні поля й бізнес-методи в domain/entities.py")
    print(f"2. Онови persistence/orm.py відповідними колонками")
    print(f"3. Онови persistence/mapper.py відповідно до нових полів")
    print(f"4. alembic revision --autogenerate -m \"add {table_name} table\"")
    print(f"5. alembic upgrade head")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python tools/create_module.py module_name")
        return
    create_module(sys.argv[1])


if __name__ == "__main__":
    main()