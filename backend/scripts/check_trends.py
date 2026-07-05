"""Перевірка trend() на реальних лабораторних даних із парними датами.

Суто технічна перевірка напрямку зміни між двома результатами одного
тесту в одного пацієнта. Не медичний висновок — лише UP/DOWN/STABLE/
INSUFFICIENT_DATA за відсотком зміни.

python scripts/check_trends.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.service import (
    LaboratoryResultNotFoundError,
    LaboratoryService,
)
from app.modules.profile.application.service import ProfileService
import app.persistence.model_registry  # noqa: F401

PATIENT_BIRTH_DATE_YEAR = 1977  # для ідентифікації профілю, як у import_dila_results.py

# Показники з парними датами (2026-05-09 і 2026-06-26) в обох PDF
TEST_CODES_WITH_HISTORY = [
    "TC",
    "LDL",
    "HDL",
    "NON_HDL",
    "TG",
    "VLDL",
]


def check_trends() -> None:
    with UnitOfWork() as uow:
        profile_service = ProfileService(uow)
        profiles = profile_service.list_profiles()
        profile = next(
            (p for p in profiles if p.birth_date and p.birth_date.year == PATIENT_BIRTH_DATE_YEAR),
            None,
        )

        if profile is None:
            print("ERROR: профіль не знайдено. Спочатку запусти import_dila_results.py")
            return

        service = LaboratoryService(uow)

        print(f"Профіль id={profile.id}\n")
        print(f"{'Тест':10} {'Останнє значення':>18} {'Інтерпретація':>16} {'Тренд':>20}")
        print("-" * 68)

        for test_code in TEST_CODES_WITH_HISTORY:
            try:
                latest, trend_direction = service.get_trend(profile.id, test_code)
                print(
                    f"{test_code:10} {latest.value!s:>18} "
                    f"{latest.interpretation.value:>16} {trend_direction.value:>20}"
                )
            except LaboratoryResultNotFoundError as exc:
                print(f"{test_code:10} — {exc}")


if __name__ == "__main__":
    check_trends()