"""Одноразовий seed-скрипт лабораторних нормативів.

Запуск: python scripts/seed_reference_ranges.py
Ідемпотентний — повторний запуск не створює дублікатів.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.uow import UnitOfWork
from app.modules.laboratory.persistence.reference_range_orm import ReferenceRangeORM
import app.persistence.model_registry  # noqa: F401

SEED_DATA = [
    dict(test_code="GLU", test_name="Glucose", unit="mmol/L", reference_min=3.9, reference_max=5.5, source="seed_v1"),
    dict(test_code="TSH", test_name="Thyroid Stimulating Hormone", unit="mIU/L", reference_min=0.4, reference_max=4.0, source="seed_v1"),
    dict(test_code="HGB", test_name="Hemoglobin", unit="g/L", sex="male", reference_min=130.0, reference_max=170.0, source="seed_v1"),
    dict(test_code="HGB", test_name="Hemoglobin", unit="g/L", sex="female", reference_min=120.0, reference_max=150.0, source="seed_v1"),

    dict(test_code="PTH", test_name="Паратгормон (1-84)", unit="пг/мл", reference_min=18.5, reference_max=88.0, source="dila"),
    dict(test_code="CA_ION", test_name="Кальцій іонізований", unit="ммоль/л", reference_min=1.09, reference_max=1.35, source="dila"),
    dict(test_code="PHOS", test_name="Фосфор", unit="ммоль/л", reference_min=0.78, reference_max=1.65, source="dila"),
    dict(test_code="TC", test_name="Загальний холестерин", unit="ммоль/л", reference_max=5.2, source="dila_esc2016"),
    dict(test_code="LDL", test_name="ХС ЛПНЩ", unit="ммоль/л", reference_max=3.0, source="dila_esc_eas2019"),
    dict(test_code="HDL", test_name="ХС ЛПВЩ", unit="ммоль/л", sex="male", reference_min=1.0, source="dila_esc2019"),
    dict(test_code="HDL", test_name="ХС ЛПВЩ", unit="ммоль/л", sex="female", reference_min=1.2, source="dila_esc2019"),
    dict(test_code="NON_HDL", test_name="ХС не-ЛПВЩ", unit="ммоль/л", reference_max=3.8, source="dila_esc_eas2019"),
    dict(test_code="TG", test_name="Тригліцериди", unit="ммоль/л", reference_max=1.7, source="dila"),
    dict(test_code="VLDL", test_name="ХС ЛПДНЩ", unit="ммоль/л", reference_min=0.26, reference_max=1.04, source="dila"),
    dict(test_code="CALCITONIN", test_name="Кальцитонін", unit="пг/мл", reference_max=12.69, source="dila"),
    dict(test_code="TSH", test_name="ТТГ (високочутлива методика)", unit="мкОд/мл",
         reference_min=0.40, reference_max=4.85, method="high_sensitive_biotin_independent", source="dila"),
    dict(test_code="VITD", test_name="25-гідроксивітамін Д", unit="нг/мл", reference_min=75, reference_max=125, source="dila_ukr_consensus_2023"),
    dict(test_code="URIC", test_name="Сечова кислота", unit="мкмоль/л", reference_min=210, reference_max=420, source="dila"),
    dict(test_code="TGB", test_name="Тиреоглобулін", unit="нг/мл", age_min=19, reference_min=1.59, reference_max=50.03, source="dila"),
    dict(test_code="FT4", test_name="Тироксин вільний", unit="нг/дл", reference_min=0.61, reference_max=1.47, source="dila"),
    dict(test_code="ATG", test_name="Антитіла до тиреоглобуліну", unit="МО/мл", reference_max=4.0, source="dila"),

    dict(test_code="PSA_TOTAL", test_name="ПСА загальний", unit="нг/мл", reference_max=2.5, source="dila"),
    dict(test_code="TESTO_TOTAL", test_name="Тестостерон загальний", unit="нмоль/л", sex="male", reference_min=5.72, reference_max=26.14, source="dila"),
    dict(test_code="SHBG", test_name="Глобулін, що зв'язує статеві гормони", unit="нмоль/л", reference_min=14.55, reference_max=94.64, source="dila"),
    dict(test_code="FREE_TESTO_INDEX", test_name="Індекс вільного тестостерону", unit="", reference_min=14.53, reference_max=80.29, source="dila"),
    dict(test_code="PRL", test_name="Пролактин", unit="нг/мл", sex="male", age_min=19, reference_min=2.64, reference_max=13.13, source="dila"),
    dict(test_code="E2", test_name="Естрадіол", unit="пг/мл", sex="male", age_min=19, reference_max=31.5, source="dila"),
    dict(test_code="FREE_TESTO", test_name="Тестостерон вільний", unit="пг/мл", sex="male", reference_min=9.57, reference_max=40.6, source="dila"),
    dict(test_code="LH", test_name="Лютеїнізуючий гормон", unit="Од/л", sex="male", age_min=19, reference_min=1.24, reference_max=8.62, source="dila"),
]


def seed() -> None:
    with UnitOfWork() as uow:
        repo = uow.repo(ReferenceRangeORM)
        existing = repo.list(limit=1000)

        def already_exists(entry: dict) -> bool:
            return any(
                row.test_code == entry["test_code"]
                and row.unit == entry["unit"]
                and row.sex == entry.get("sex")
                and row.age_min == entry.get("age_min")
                and row.age_max == entry.get("age_max")
                and row.method == entry.get("method")
                for row in existing
            )

        added = 0
        for entry in SEED_DATA:
            if already_exists(entry):
                print(f"SKIP (вже існує): {entry['test_code']} {entry.get('sex', 'будь-яка стать')}")
                continue
            uow.session.add(ReferenceRangeORM(**entry))
            added += 1
            print(f"OK: додано {entry['test_code']} ({entry['unit']}, {entry.get('sex', 'будь-яка стать')})")

        uow.commit()
        print(f"\nУсього додано нових записів: {added}")


if __name__ == "__main__":
    seed()