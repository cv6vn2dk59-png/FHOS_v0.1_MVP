$root = 'D:\FHOS\FHOS_v0.1_MVP'
@'
# PostgreSQL Compatibility Checklist

Документ, не автоматизація. Виконати ПЕРЕД тим, як назвати будь-який модуль "production-ready" (Constitution: PostgreSQL — основна БД, SQLite — тимчасова).

Створено за підсумком Devil Review Sprint 3 (Laboratory + Reference Range), перевірені лише на SQLite dev-базі.

## 1. Enum serialization
- Перевір, як Alembic autogenerate генерує enum для PostgreSQL (реальний `CREATE TYPE`, не text+CHECK, як на SQLite).
- Підтверди, що values_callable (lowercase) зберігається так само коректно, як на SQLite.
- Перевір конфлікт, якщо enum type з такою назвою вже існує (PostgreSQL enum типи — іменовані об'єкти на рівні схеми, не просто constraint).
- Перевір `downgrade()` — чи коректно видаляє enum type, не тільки колонку.

## 2. CHECK constraints
- `ck_laboratory_results_interpretation_valid`, `ck_reference_ranges_min_max` — перевір синтаксис і поведінку на PostgreSQL (відрізняється від SQLite).
- Перевір naming conventions constraint — PostgreSQL має обмеження довжини імені (63 символи).

## 3. Foreign Keys
- У SQLite потрібен явний `PRAGMA foreign_keys=ON` (за замовчуванням вимкнено). У PostgreSQL FK завжди активні.
- Це може виявити помилки, які SQLite мовчки пропускав (наприклад, вставка з невалідним FK, якщо PRAGMA десь не був увімкнений).

## 4. ON DELETE SET NULL
- `patient_profile_id` в `laboratory_results` — перевір реальну поведінку на PostgreSQL при видаленні `PatientProfileORM`.
- Будь-які майбутні FK з тією ж поведінкою (наприклад, якщо з'явиться `reference_range_id`).

## 5. Transactions / IntegrityError rollback
- PostgreSQL: після помилки в транзакції вона переходить у "failed" стан і вимагає явного rollback перед подальшими операціями в тій самій транзакції (SQLite більш поблажливий).
- Перевір, що `UnitOfWork.rollback()` викликається коректно в `LaboratoryService.create_result()` після `IntegrityError` — саме туди, де вже є `try/except`.

## 6. Indexes
- Перевір, що індекси реально створюються на PostgreSQL: `ix_laboratory_results_patient_test_date`, `ix_reference_ranges_test_code`, `ix_reference_ranges_test_code_unit`.
- PostgreSQL чутливіший до query plan — розглянь `EXPLAIN ANALYZE` для запитів `ReferenceRangeRepository.get_candidates()` при реальному обсязі даних.

## Статус виконання
Не виконано. Виконати перед першим production deployment або першим модулем, що явно вимагає PostgreSQL-специфічної поведінки.
'@ | Out-File -Encoding utf8 "$root\docs\DEVELOPER_GUIDE\PostgreSQL Compatibility Checklist.md"
