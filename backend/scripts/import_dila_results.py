"""Імпорт реальних лабораторних результатів пацієнта (2 PDF Dila).

python scripts/import_dila_results.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.service import LaboratoryService
from app.modules.laboratory.schemas.laboratory import LaboratoryResultCreate
from app.modules.profile.application.service import ProfileService
from app.modules.profile.schemas.profile import PatientProfileCreate
from app.shared.dates import calculate_age
import app.persistence.model_registry  # noqa: F401

PATIENT_BIRTH_DATE = date(1977, 5, 20)
PATIENT_SEX = "male"

RESULTS = [
    ("PTH", "Паратгормон (1-84)", "пг/мл", 44.1, date(2026, 5, 9), None, None),
    ("CA_ION", "Кальцій іонізований", "ммоль/л", 1.14, date(2026, 5, 9), None, None),
    ("PHOS", "Фосфор", "ммоль/л", 1.18, date(2026, 5, 9), None, None),
    ("TC", "Загальний холестерин", "ммоль/л", 7.47, date(2026, 5, 9), None, None),
    ("LDL", "ХС ЛПНЩ", "ммоль/л", 5.37, date(2026, 5, 9), None, None),
    ("HDL", "ХС ЛПВЩ", "ммоль/л", 1.50, date(2026, 5, 9), None, None),
    ("NON_HDL", "ХС не-ЛПВЩ", "ммоль/л", 5.97, date(2026, 5, 9), None, None),
    ("TG", "Тригліцериди", "ммоль/л", 1.12, date(2026, 5, 9), None, None),
    ("VLDL", "ХС ЛПДНЩ", "ммоль/л", 0.51, date(2026, 5, 9), None, None),
    ("CALCITONIN", "Кальцитонін", "пг/мл", 2.0, date(2026, 5, 9), "PDF: <2 (нижче межі виявлення)", None),
    ("TSH", "ТТГ (високочутлива методика)", "мкОд/мл", 0.131, date(2026, 5, 9), None, "high_sensitive_biotin_independent"),
    ("VITD", "25-гідроксивітамін Д", "нг/мл", 93.0, date(2026, 5, 9), "Одиниця припущена, не вказана явно в PDF", None),
    ("URIC", "Сечова кислота", "мкмоль/л", 455.0, date(2026, 5, 9), None, None),
    ("TGB", "Тиреоглобулін", "нг/мл", 0.2, date(2026, 5, 9), None, None),
    ("FT4", "Тироксин вільний", "нг/дл", 1.17, date(2026, 5, 9), None, None),
    ("ATG", "Антитіла до тиреоглобуліну", "МО/мл", 0.9, date(2026, 5, 9), "PDF: <0.9 (нижче межі виявлення)", None),

    ("TC", "Загальний холестерин", "ммоль/л", 6.77, date(2026, 6, 26), None, None),
    ("LDL", "ХС ЛПНЩ", "ммоль/л", 4.99, date(2026, 6, 26), None, None),
    ("HDL", "ХС ЛПВЩ", "ммоль/л", 1.55, date(2026, 6, 26), None, None),
    ("NON_HDL", "ХС не-ЛПВЩ", "ммоль/л", 5.22, date(2026, 6, 26), None, None),
    ("TG", "Тригліцериди", "ммоль/л", 0.95, date(2026, 6, 26), None, None),
    ("VLDL", "ХС ЛПДНЩ", "ммоль/л", 0.44, date(2026, 6, 26), None, None),
    ("PSA_TOTAL", "ПСА загальний", "нг/мл", 0.23, date(2026, 6, 26), None, None),
    ("TESTO_TOTAL", "Тестостерон загальний", "нмоль/л", 5.70, date(2026, 6, 26), None, None),
    ("SHBG", "Глобулін, що зв'язує статеві гормони", "нмоль/л", 28.4, date(2026, 6, 26), None, None),
    ("FREE_TESTO_INDEX", "Індекс вільного тестостерону", "", 20.07, date(2026, 6, 26), None, None),
    ("PRL", "Пролактин", "нг/мл", 11.54, date(2026, 6, 26), None, None),
    ("E2", "Естрадіол", "пг/мл", 19.20, date(2026, 6, 26), None, None),
    ("FREE_TESTO", "Тестостерон вільний", "пг/мл", 8.39, date(2026, 6, 26), None, None),
    ("GLU", "Глюкоза (кількісний)", "mmol/L", 5.0, date(2026, 6, 26), "PDF: 4.0-5.5; резолвиться проти seed 3.9-5.5", None),
    ("LH", "Лютеїнізуючий гормон", "Од/л", 2.87, date(2026, 6, 26), None, None),
]


def import_results() -> None:
    with UnitOfWork() as uow:
        profile_service = ProfileService(uow)
        profiles = profile_service.list_profiles()
        profile = next((p for p in profiles if p.birth_date == PATIENT_BIRTH_DATE), None)

        if profile is None:
            profile = profile_service.create_profile(PatientProfileCreate(
                first_name="Тестовий", last_name="Пацієнт",
                birth_date=PATIENT_BIRTH_DATE, sex=PATIENT_SEX,
            ))
            print(f"OK: створено профіль id={profile.id}")
        else:
            print(f"OK: використано існуючий профіль id={profile.id}")
        profile_id = profile.id

    with UnitOfWork() as uow:
        service = LaboratoryService(uow)
        for test_code, test_name, unit, value, result_date, notes, method in RESULTS:
            age = calculate_age(PATIENT_BIRTH_DATE, as_of=result_date)
            data = LaboratoryResultCreate(
                patient_profile_id=profile_id, test_name=test_name, test_code=test_code,
                unit=unit, value=value, result_date=result_date, notes=notes, method=method,
            )
            result = service.create_result(data, sex=PATIENT_SEX, age=age)
            status = result.reference_range_status.value if result.reference_range_status else "н/д"
            print(f"{test_code:20} {value:>8} {unit:10} -> {result.interpretation.value:15} "
                  f"[{status}] score={result.abnormality_score()}")


if __name__ == "__main__":
    import_results()