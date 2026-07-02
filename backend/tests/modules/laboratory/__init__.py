from app.persistence.base import Base
from app.persistence.system import SystemLog
from app.modules.profile.persistence.orm import PatientProfileORM
from app.modules.laboratory.persistence.orm import LaboratoryResultORM
from app.modules.laboratory.persistence.repository import LaboratoryRepository  # noqa: F401 — реєструє в RepositoryRegistry

__all__ = [
    "Base",
    "SystemLog",
    "PatientProfileORM",
    "LaboratoryResultORM",
    "LaboratoryRepository",
]