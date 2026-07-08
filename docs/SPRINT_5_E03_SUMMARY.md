# FHOS S05E03 — Drug Interactions — Seed Script + Consistency Review

Дата: 2026-07-08
Статус: Виконано.

## 1. Seed script (backlog з SPRINT_5_E02_SUMMARY.md)

`backend/scripts/seed_phansalkar_data.py` -- за зразком
`seed_reference_ranges.py`:

- Ідемпотентний: дублікати визначаються через `DrugInteraction.pair_key()`
  (нормалізована симетрична пара), не через SQL-рівність JSON-колонок
  side_a/side_b -- та сама взаємодія технічно могла б бути записана у
  двох різних текстових формах.
- Після запуску `DrugInteractionService._load_known_interactions()`
  читає з таблиці `drug_interactions` замість fallback на
  `PHANSALKAR_2013_INTERACTIONS` у пам'яті.

Перевірено (венв проєкту недоступний з цієї сесії -- див. розділ 3):
перший запуск додав 15/15 записів, другий запуск -- 0/15 (усі 15
розпізнані як SKIP), фінальний рядковий підрахунок у таблиці: 15.

## 2. Consistency Review Drug Interactions (за зразком Laboratory, Sprint 4)

Проглянуто весь модуль (domain, persistence, application, api, schemas,
tests) проти Constitution v3.1 і рішень ADR-0012, S05E01, S05E02.

### Виправлено одразу (низький ризик, без архітектурних наслідків)

1. **`PatientInteractionNoteORM.note_text` дублював ліміт 2000 як
   окреме число** (`String(2000)`), тоді як domain-константа
   `MAX_PATIENT_NOTE_LENGTH` і Pydantic-схема вже посилались на єдине
   джерело. Той самий клас ризику, що вже задокументований у backlog
   для `LaboratoryResultCreate.validate_reference_range()` -- зміна
   ліміту в domain мовчки розійшлася б з реальним обмеженням у БД.
   Виправлено: колонка тепер `String(MAX_PATIENT_NOTE_LENGTH)` з
   явним коментарем у коді. Alembic-міграція (point-in-time snapshot)
   лишається з захардкодженим числом -- це нормально і відповідає
   конвенції всіх існуючих міграцій проєкту.

2. **`PatientInteractionNote.created_at` мав тип `"object"`** замість
   `"datetime | None"`, на відміну від усіх сусідніх domain-класів у
   тому ж файлі (`MedicationRecord`, `PrescriptionHistoryEntry`
   використовують конкретний тип `"date"`/`"date | None"`).
   `from __future__ import annotations` вже активний у файлі, тож
   анотації однаково не обчислюються під час виконання -- зміна
   безпечна і не впливає на поведінку, лише на точність типу для
   читача/type checker'а. Виправлено.

### Виправлено після рішення користувача (2026-07-08, ретроспективна нотатка)

4. **`substance_a`/`substance_b` у patient_note тепер проходять через
   `normalize_drug_name()`** у `DrugInteractionService.create_patient_note()`
   -- той самий name_mapping, що вже використовує
   `check_active_medications()`/`find_prescription_history()`. Рішення
   користувача: нормалізація назви -- технічна операція, спільна для
   всіх трьох блоків Evidence View; "не перевірено" для patient_note
   стосується змісту нотатки, а не написання назви речовини. Наслідок:
   `pair_key()` нотатки тепер збігається з `pair_key()`
   verified_interaction для тієї самої пари речовин, незалежно від
   того, якою мовою/формою пацієнт її ввів ("варфарин" чи "warfarin").

   Побічний ефект (позитивний, виявлений тестом): нормалізація до
   побудови domain-об'єкта тепер ловить колізію на рівні речовини, а
   не лише рядка -- "кордарон" і "аміодарон" (два різні написання
   amiodarone) коректно викликають `ValueError` про самовзаємодію,
   хоча раніше внутрішня `_normalize()` (просто lower/strip) цього не
   бачила.

   Свідомий компроміс: оригінальне написання пацієнта (наприклад,
   бренд "кордарон") НЕ зберігається окремо -- у полях substance_a/
   substance_b лишається лише нормалізована INN-назва. На відміну від
   `PrescriptionHistoryEntry`, де є ОКРЕМІ поля для оригінальної назви
   (`medication_a_name`) і нормалізованої речовини (`substance_a`),
   `PatientInteractionNote` такого розділення не має -- додавання
   другого поля означало б зміну схеми/ORM/міграції заради
   гіпотетичної потреби показати пацієнту його власне формулювання.
   Відкладено до Confirmed Repetition (реального запиту показати
   оригінальний ввід).

   Тести: 3 нових (`test_normalizes_brand_names_on_creation`,
   `test_pair_key_matches_across_brand_and_inn_naming`,
   `test_raises_when_different_brand_names_normalize_to_same_substance`)
   у `test_patient_note_service.py`.

### Ідентифіковано, НЕ виправлено (потребує рішення, не мій виклик)

3. **`PatientInteractionNote.pair_key()` не має жодного споживача**
   у application/API шарі -- `list_patient_notes()` повертає всі
   нотатки пацієнта без фільтрації за парою, `pair_key()`
   використовується лише в тестах. Той самий патерн, що вже в backlog
   PROJECT_STATE.md для `LaboratoryRepository.get_latest_result()`
   ("unused, рішення не прийнято"). Варіанти: (a) залишити як є --
   метод дешевий, задокументований, готовий для майбутнього
   фільтра "нотатки саме для цієї пари речовин"; (b) прибрати, поки
   немає Confirmed Repetition (принцип із PROJECT_STATE.md). Не
   вирішую сам -- як і попередній аналогічний випадок, залишаю
   відкритим. (Тепер із пункту 4 вище — pair_key() коректно порівнює
   нормалізовані назви, тож ця абстракція стала ще ближчою до реальної
   потреби, якщо/коли з'явиться фільтр за парою.)

5. **Неоднорідність Optional-типізації в `DrugInteractionService`**:
   нові методи (`list_patient_notes(patient_profile_id: int | None)`)
   типізовано коректно, тоді як існуючі `check_active_medications`/
   `find_prescription_history` мають анотацію `patient_profile_id: int`
   (без `| None`), хоча тести викликають їх з `None`. Той самий патерн
   вже є в `MedicationService.list_medications_for_patient` -- це
   projектна конвенція, що вийшла за межі одного модуля, не помилка,
   яку варто тихо виправляти лише в Drug Interactions без узгодження
   на рівні всього проєкту.

6. **`domain/entities.py` продовжує рости**: тепер містить
   `DrugInteraction`, `MedicationRecord`, `PrescriptionHistoryEntry`,
   `PatientInteractionNote` в одному файлі (199 рядків). Не порушення
   Constitution саме зараз, але кандидат на розділення за
   відповідальністю (по одному domain-об'єкту на файл, за зразком
   Laboratory), якщо файл продовжить рости при майбутніх Drug
   Interactions features.

## 3. Реальна перевірка командами -- обмеження цієї сесії

Ця сесія працює в ізольованому Linux-середовищі без доступу до
`D:\FHOS\FHOS_v0.1_MVP` -- спроба змонтувати теку в bash-пісочницю
відхилена середовищем (підтверджено двічі). Тому:

- `git status`, `git log`, `alembic current` -- НЕ виконано з цієї
  сесії. Я не бачу реального стану git/Alembic на вашій машині і не
  видаю жодних тверджень про нього.
- Реальний `pytest` у вашому venv -- також не виконано звідси.
  Натомість: увесь зачеплений код (domain/persistence/application/
  schemas/api для patient_note + seed-скрипт) відтворено файл-у-файл
  в ізольованому Linux venv, `pip install` свіжих залежностей з
  `requirements.txt`, і прогнано `python -m pytest tests/ -v` -- 18/18
  passed, плюс окремий прогін ідемпотентності seed-скрипта (15 доданих
  → 15 пропущено при повторному запуску) і FastAPI TestClient
  смоук-тест (create/400/422/evidence, з попередньої сесії). Це
  підтверджує коректність логіки, але це НЕ те саме, що прогін у
  вашому реальному репозиторії з вашою реальною історією комітів.

### Команди для реальної перевірки у вашому venv

```powershell
cd D:\FHOS\FHOS_v0.1_MVP
git status
git log --oneline -10

cd backend
.venv\Scripts\activate
alembic current
alembic upgrade head
python -m pytest tests/ -v
python scripts/seed_phansalkar_data.py
```

Очікування: `alembic current` після `upgrade head` показує `9a3d7c1f2b6e`;
`pytest` -- усі тести проходять (раніше 28/28 для Drug Interactions,
+ 14 нових для patient_note = 42, плюс решта модулів проєкту); seed
script -- 15 додано при першому запуску.

**Підтверджено користувачем 2026-07-08** (реальний venv, не ізольоване
середовище): `git status`/`git log` відповідають очікуваним змінам,
`alembic current` -- `9a3d7c1f2b6e` (head), `python -m pytest tests/ -v`
-- 147/147 passed, seed script -- 15/15 додано. Після цього внесено
нормалізацію substance_a/substance_b (пункт 4 вище) -- ця конкретна
зміна повторно перевірена лише в ізольованому середовищі (11/11 passed,
включно з 3 новими тестами), НЕ у вашому реальному venv -- перед
комітом варто ще раз прогнати `pytest tests/ -v` для підтвердження
147+3 = 150 passed.
