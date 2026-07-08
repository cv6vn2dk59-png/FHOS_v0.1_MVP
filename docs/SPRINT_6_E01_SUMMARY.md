# FHOS S06E01 — Diseases v1 — Architect Session + Implementation

Дата: 2026-07-08
Статус: Vertical Slice завершено. Підтверджено лише в ізольованому
Linux-середовищі — очікує підтвердження в реальному venv користувача
(команди наприкінці цього файлу).

## Architect Session (без коду, у чаті)

Confirmed Repetition для Diseases підтверджено фактами, не лише
обговоренням: SPRINT_5_E01 (п.1) явно виключає "препарат-хвороба" зі
scope Drug Interactions v1 з формулюванням "кожен зв'язок має власне
джерело даних" (перше спливання); PROJECT_STATE.md називає Diseases
модулем, потрібним для другого підтвердження кандидат-принципу "Three
Levels of Thinking" (Medications — перше). Формат сесії — дзеркально
до ADR-0009 (Medications): Architect Mode, потім Implementation Mode.

Рішення користувача (усі підтверджені без контрприкладів):

1. **Scope v1**: лише факт наявності діагнозу в часі (`is_active()`,
   `onset_date`/`resolved_date`) — аналог `is_active()`/`duration_days()`
   у Medications. НЕ робимо зараз: drug↔disease contraindications,
   Age-Typicality Score, Clinical Context Override — усі три в
   FUTURE_IDEAS.md, жоден без другого підтвердження. Contraindications —
   майбутній окремий Knowledge-модуль (прецедент Drug Interactions),
   що читає facts з Diseases v1 + Medications v1, не змінюючи їх.
2. **Ідентифікатор**: вільний текст (`diagnosis_name`), Ukrainian-first
   (ADR-0002). `icd_code` — опціональне nullable поле для майбутнього
   мапування (той самий підхід, що `drug_name`/`atc_code` у Medications,
   ADR-0012). ICD-10 з самого початку як обов'язкове поле відхилено —
   блокує ввід без довідника кодів, суперечить offline/Ukrainian-first.
3. **Cross-module залежності**: жодних, як у Medications v1. FK на
   PatientProfile з `ondelete=SET NULL`, без виклику ProfileService.
4. **Статусна модель**: лише `resolved_date` (nullable), без третього
   статусу (`chronic`). `resolved_date=None` = "хронічне/триває
   дотепер" — та сама семантика, що вже працює для `end_date=None` у
   Medications. Третій статус відхилено: вимагав би нової логіки ("хто
   і коли встановлює") без Confirmed Repetition. Якщо колись
   знадобиться розрізняти "хронічне за визначенням" від "просто ще не
   закрите" — окреме нове поле (`is_chronic: bool`) при реальній
   потребі, не заміна моделі зараз.

Повне обґрунтування й наслідки — ADR-0013.

## Implementation Mode

- **Domain** (`app/modules/diseases/domain/entities.py`): `Disease`
  dataclass — `diagnosis_name`, `onset_date`, `icd_code`,
  `resolved_date`, `notes`, `is_active()`, `duration_days()`. Валідація:
  `resolved_date < onset_date` → `ValueError`.
- **Persistence**: `DiseaseORM` (таблиця `diseases`, FK на
  `patient_profiles.id` ON DELETE SET NULL, `CheckConstraint` дзеркально
  до Medications), `mapper.py` (`to_domain`/`to_orm`),
  `DiseaseRepository.get_diseases_for_patient()`.
- **Application**: `DiseaseService.create_disease()` /
  `list_diseases_for_patient()`, `InvalidPatientReferenceError` (той
  самий патерн, що Medications/Drug Interactions).
- **Schemas**: `DiseaseCreate` (з `model_validator` на дати),
  `DiseaseRead` (`from_attributes=True`, як у `MedicationRead`).
- **API**: `POST /diseases/`, `GET /diseases/patient/{id}`.
- **Реєстрація**: `app/persistence/model_registry.py`,
  `app/api/router.py`.
- **Alembic**: міграція `e4f6a8c1d3b5`, `down_revision=9a3d7c1f2b6e`
  (попередній head).
- **ADR-0013**: Diseases v1 Domain Scope (дзеркало ADR-0009).

## Тести

- `tests/modules/diseases/test_diseases_domain.py` — 11 тестів
  (валідація дат, `is_active()` на межах, `duration_days()`,
  `icd_code` за замовчуванням/явно заданий).
- `tests/modules/diseases/test_service.py` — 4 тести
  (`InvalidPatientReferenceError`, успішне створення з
  `patient_profile_id=None`, список для пацієнта, порожній список).

## Перевірка (обмеження сесії — немає доступу до D:\FHOS з бекенду)

Увесь зачеплений код відтворено файл-у-файл в ізольованому Linux
venv (свіжі залежності з `requirements.txt` + pytest): 15/15 тестів
passed. Додатково окремий FastAPI `TestClient` смоук-тест: create → 201
(з коректним `resolved_date: null`), invalid `patient_profile_id` → 400,
list → 200. Alembic-міграція перевірена на синтаксис (`py_compile`) і
структурно ідентична вже підтвердженій міграції Medications — REAL
`alembic upgrade head` у цій сесії НЕ виконувався.

### Команди для реальної перевірки у вашому venv

```powershell
cd D:\FHOS\FHOS_v0.1_MVP\backend
alembic upgrade head
python -m pytest tests/ -v
```

Очікування: `alembic current` → `e4f6a8c1d3b5` (head); pytest —
150 (попередніх, Sprint 5) + 15 нових (Diseases) = 165 passed.

## Наступна робота
- Contraindications (drug↔disease) — окремий майбутній Knowledge-
  модуль, Architect Session за прецедентом Drug Interactions, коли
  з'явиться конкретний запит.
- Seed/приклади даних для Diseases — не потрібні зараз (на відміну від
  Drug Interactions, тут немає зовнішнього джерела на кшталт
  Phansalkar 2013 для v1).
