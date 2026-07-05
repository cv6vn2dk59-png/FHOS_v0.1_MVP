$root = 'D:\FHOS\FHOS_v0.1_MVP'
@'
# Testing Guide

## Принцип
Constitution: кожна бізнес-логіка має автотести, особливо клінічні правила. Швидкі unit-тести пріоритетніші за складні інтеграційні, якщо unit-тестів достатньо.

## Структура тестів модуля (за зразком Laboratory)
- `test_<module>_domain.py` — Domain-логіка, межові випадки (нормальні значення, None/відсутні дані, точні межі діапазонів по обидва боки).
- `test_service.py` — Application Service, exception handling (наприклад InvalidPatientReferenceError).
- `test_service_<feature>_integration.py` — інтеграційні сценарії, що вимагають реальної (in-memory) БД.

## In-memory SQLite fixture — обов'язковий PRAGMA
FK constraints не працюють у SQLite без явного вмикання. Кожна in-memory fixture, що тестує FK-залежну поведінку, повинна містити:
```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def _enable_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```
Без цього тести на FK-порушення (`IntegrityError`) мовчки не спрацюють — `DID NOT RAISE` замість очікуваного виключення.

## Межові випадки — обов'язкові для будь-якої шкали/порогу
Для кожного числового порогу (наприклад, abnormality_score 10%/30%/50%) — тест рівно на межі, тест щойно вище межі, тест щойно нижче межі, з обох боків (позитивне і негативне відхилення).

## Перед кожним `python -m pytest tests/ -v`
Порівнюй фактичну кількість `collected N items` з очікуваною — не вір своєму підрахунку заздалегідь, довіряй виводу pytest.
'@ | Out-File -Encoding utf8 "$root\docs\DEVELOPER_GUIDE\Testing Guide.md"