from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
MODULES_DIR = APP_DIR / "modules"


TEMPLATE_FILES = {
    "__init__.py": "",
    "api/__init__.py": "",
    "api/routes.py": '''from fastapi import APIRouter


router = APIRouter(prefix="/{route_prefix}", tags=["{module_title}"])


@router.get("/health")
def module_health():
    return {{
        "status": "ok",
        "module": "{module_name}",
    }}
''',
    "application/__init__.py": "",
    "application/service.py": '''class {class_name}Service:
    pass
''',
    "domain/__init__.py": "",
    "domain/entities.py": '''from dataclasses import dataclass


@dataclass
class {class_name}:
    pass
''',
    "persistence/__init__.py": "",
    "persistence/orm.py": '''from app.persistence.base import Base


class {class_name}ORM(Base):
    __tablename__ = "{table_name}"

    __abstract__ = True
''',
    "schemas/__init__.py": "",
    "schemas/{module_name}.py": '''from pydantic import BaseModel


class {class_name}Create(BaseModel):
    pass


class {class_name}Read(BaseModel):
    pass
''',
}


def to_class_name(module_name: str) -> str:
    return "".join(part.capitalize() for part in module_name.split("_"))


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

    print(f"OK: module created: app/modules/{module_name}")
    print()
    print("Next steps:")
    print(f"1. Import router in app/api/router.py:")
    print(
        f"   from app.modules.{module_name}.api.routes import router as {module_name}_router"
    )
    print(f"2. Add:")
    print(f"   api_router.include_router({module_name}_router)")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python tools/create_module.py module_name")
        return

    create_module(sys.argv[1])


if __name__ == "__main__":
    main()