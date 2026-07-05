"""Ручна перевірка одного лабораторного результату через реальний Service.

Використання: підстав значення у VALUE / TEST_CODE / UNIT / SEX / AGE
нижче (взяті з PDF аналізу) і запусти скрипт.

python scripts/verify_lab_result.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.service import LaboratoryService
from app.modules.laboratory.schemas.laboratory import LaboratoryResultCreate
import app.persistence.model_registry  # noqa: F401

# --- Підстав дані з PDF сюди ---
TEST_CODE = "GLU"
TEST_NAME = "Glucose"
UNIT = "mmol/L"
VALUE = 6.2
SEX = "male"
AGE = 45
RESULT_DATE = date(2026, 7, 5)
# --------------------------------


def verify() -> None:
    with UnitOfWork() as uow:
        service = LaboratoryService(uow)
        data = LaboratoryResultCreate(
            test_name=TEST_NAME,
            test_code=TEST_CODE,
            unit=UNIT,
            value=VALUE,
            result_date=RESULT_DATE,
        )
        result = service.create_result(data, sex=SEX, age=AGE)

        print(f"Тест:                {result.test_name} ({result.test_code})")
        print(f"Значення:            {result.value} {result.unit}")
        print(f"Референс:            {result.reference_min}–{result.reference_max}")
        print(f"Статус референсу:    {result.reference_range_status.value if result.reference_range_status else 'н/д'}")
        print(f"Інтерпретація:       {result.interpretation.value}")
        print(f"Abnormality score:   {result.abnormality_score()}")


if __name__ == "__main__":
    verify()