# FHOS S06E02 — Diseases v1 — Live API Verification + Consistency Review

Дата: 2026-07-08
Статус: Виконано.

## 1. Live API Verification (не лише pytest)

Реальний виклик ендпоінтів через FastAPI `TestClient`, змонтований на
справжній `app.modules.diseases.api.routes.router` (той самий router,
що зареєстрований у `app/api/router.py`), з `in_memory` SQLite замість
реальної БД -- 8 сценаріїв, усі відповідають очікуванню:

1. Створення з усіма полями (`icd_code` заданий) -- 201.
2. Створення мінімальне (без `icd_code`/`notes`) -- 201, `icd_code: null`.
3. Неіснуючий `patient_profile_id=999` -- 400 з коректним повідомленням.
4. Відсутнє обов'язкове поле `onset_date` -- 422.
5. `resolved_date` раніше `onset_date` -- 422 (спрацював
   `DiseaseCreate.validate_dates()`).
6. `resolved_date == onset_date` (межа) -- 201, дозволено.
7. `GET /diseases/patient/{id}` для профілю без записів -- 200, `[]`.
8. `diagnosis_name` довжиною 256 символів (ліміт 255) -- 422.

Сценарії 5/6/8 виявили реальну прогалину: жоден існуючий тест не
перевіряв `DiseaseCreate` напряму (лише `Disease.__post_init__` на
domain-рівні). Закрито в межах цього ж проходу -- див. розділ 2.

**Обмеження**: перевірено ізольований router + справжній код Diseases
(файл-у-файл з реального репозиторію), НЕ повний `app.main:app` з усіма
модулями (Laboratory, Imaging, legacy `api_core` тощо) -- повна
реконструкція всього застосунку в цій сесії не виконувалась. `pytest`
165/165 (підтверджено користувачем у реальному venv) уже опосередковано
перевіряє імпорт `model_registry.py` з усіма модулями разом, що покриває
більшість ризику "чи взагалі стартує застосунок". Якщо потрібна повна
певність саме для `app.main:app`, ось одноразовий скрипт для вашого
venv (не для коміту в git -- одноразова перевірка):

```python
# verify_diseases_live.py -- запустити з backend/, видалити після використання
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.persistence.base import Base
import app.persistence.model_registry  # noqa: F401

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)

@event.listens_for(engine, "connect")
def _fk(dbapi_connection, connection_record):
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()

Base.metadata.create_all(engine)
SessionFactory = sessionmaker(bind=engine)

def override_get_uow():
    with UnitOfWork(session_factory=SessionFactory) as uow:
        yield uow

app.dependency_overrides[get_uow] = override_get_uow
client = TestClient(app)

r = client.post("/api/diseases/", json={
    "diagnosis_name": "Гіпертонічна хвороба", "icd_code": "I10", "onset_date": "2026-01-01",
})
print("CREATE", r.status_code, r.json())
assert r.status_code == 201

r2 = client.get("/api/diseases/patient/1")
print("LIST", r2.status_code, r2.json())
assert r2.status_code == 200

print("app.main:app REAL WIRING CONFIRMED")
```

Важливо: `in_memory`-БД тут через `dependency_overrides`, тому
реальний `fhos_local.db` НЕ зачіпається -- безпечно запускати без
ризику для існуючих даних.

## 2. Consistency Review Diseases v1 (за зразком Laboratory/Drug Interactions)

### Виправлено

1. **`DiseaseCreate.validate_dates()` дублював domain-інваріант без
   коментаря** -- той самий клас проблеми, що вже задокументований для
   `LaboratoryResultCreate.validate_reference_range()`
   (PROJECT_STATE.md backlog), і той самий, що досі БЕЗ коментаря в
   `MedicationCreate.validate_dates()` (Medications v1 -- не займав,
   поза межами цього завдання). Додано явний коментар у коді, що
   пояснює навмисність дублювання (fail-fast на межі API).
2. **Відсутнє тестове покриття схемного валідатора** -- жоден тест не
   викликав `DiseaseCreate` напряму до цієї сесії. Додано
   `TestSchemaValidation` (3 тести) у `test_service.py`.

### Ідентифіковано, НЕ виправлено (потребує рішення, не мій виклик)

3. **Devil Review -- `diagnosis_name` як вільний текст без будь-якого
   name_mapping (на відміну від Medications)**: коли Drug Interactions
   потребував нормалізації назв препаратів, `name_mapping.py` вже
   існував як окремий, малий, добре обмежений компонент (ADR-0012).
   У Diseases v1 такого компонента НЕМАЄ навіть у зародковому вигляді
   -- якщо майбутній Contraindications-модуль (наступний Architect
   Session, за вашим власним порядком: спершу 1 і 2, лише потім
   Contraindications) захоче зіставляти `diagnosis_name` із класами
   хвороб (наприклад "подагра" для протипоказання
   фебуксостат+азатіоприн), йому доведеться створювати таку
   нормалізацію з нуля, без прецеденту. Це не помилка v1 (мета --
   не будувати абстракцію наперед, ADR-0013), але варто мати на увазі
   як конкретний, не гіпотетичний виклик наступної Architect Session,
   а не просто "colissible normalization issue" загалом.
4. **API-level (TestClient) тести не є частиною Testing Guide** --
   `docs/DEVELOPER_GUIDE/Testing Guide.md` описує лише
   `test_<module>_domain.py` / `test_service.py` /
   `test_service_<feature>_integration.py`. Жоден модуль проєкту
   (Laboratory, Medications, Drug Interactions, Diseases) не має
   постійних API-рівня тестів у git -- лише domain/application
   integration з in-memory UnitOfWork, обходячи FastAPI-шар повністю.
   Це означає, що жодна автоматизована перевірка не покриває
   `response_model`, HTTP-статуси, серіалізацію Pydantic -- усе це
   перевірено зараз лише одноразовим скриптом (розділ 1), не
   постійним тестом. Питання для явного рішення: чи вводити API-рівня
   тести як новий постійний шар Testing Guide (з відповідним
   оновленням документа), чи свідомо покладатися на
   domain+service рівень і одноразові перевірки при потребі. НЕ
   вирішую сам -- це рішення про testing strategy всього проєкту, не
   про Diseases.
5. **Optional-типізація `patient_profile_id`** у
   `DiseaseService.create_disease`/`list_diseases_for_patient` --
   `int` без `| None`, хоча тести й API (шлях `/patient/{id}`) завжди
   передають конкретний int або None у тестах. Той самий вже
   задокументований project-wide backlog (PROJECT_STATE.md), Diseases
   коректно віддзеркалює існуючу (хай і недосконалу) конвенцію
   Medications -- нічого нового, не окрема проблема цього модуля.

## Тести (підсумок)
- `test_diseases_domain.py`: 11 (без змін).
- `test_service.py`: було 4, додано `TestSchemaValidation` (3) = 7.
- Разом для Diseases: 18 (було 15 у S06E01).

## Перевірка -- обмеження цієї сесії

Як і раніше: немає доступу до `D:\FHOS\FHOS_v0.1_MVP` з бекенду цієї
сесії. Live API Verification (розділ 1) виконано на реальному коді
Diseases, відтвореному файл-у-файл в ізольованому Linux-середовищі,
НЕ у вашому venv. Нові тести (`TestSchemaValidation`) також перевірені
лише ізольовано (прямий виклик `DiseaseCreate` без БД -- усі 3 пройшли).

### Команди для реальної перевірки

```powershell
cd D:\FHOS\FHOS_v0.1_MVP\backend
python -m pytest tests/ -v
```

Очікування: 165 (попередніх) + 3 нових (`TestSchemaValidation`) = 168
passed.

## Наступна робота
- Пункт 3 (Devil Review finding) -- взяти до уваги в наступній Architect
  Session Contraindications: чи потрібен мінімальний name_mapping-подібний
  компонент для diagnosis_name з самого початку, чи це справді
  Confirmed Intention без Confirmed Repetition (як зараз вважається).
- Пункт 4 (API-testing strategy) -- окреме рішення, не тільки для
  Diseases: чи оновлювати Testing Guide новим тестовим шаром.
- Contraindications -- Architect Session, ЛИШЕ після явного підтвердження
  користувачем, що пункти 1 і 2 цього документа закриті задовільно
  (за вашим власним порядком дій).
