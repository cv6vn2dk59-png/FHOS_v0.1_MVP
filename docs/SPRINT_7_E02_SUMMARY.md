# Sprint 7 E02 -- ICD-11 v1: Architect Session + Implementation (без importer-а)

## Контекст
Завдання прийшло сформульованим ("Завдання для Cowork: ICD-11 module
v1") з посиланням на два артефакти, яких не виявилось у підключеній
теці на момент виконання: `ICD11_Chapter01_structure.xlsx` і розділ
про ліцензування ICD-11 у `PROJECT_STATE.md`. Обидва, судячи з усього,
існують в іншій сесії/розмові. Зафіксовано явно (не обійдено мовчки) --
деталі в ADR-0015, розділ "Відкрите питання".

## Architect-рівня рішення (з завдання, без заперечень)
1. Асиметрична модель, окрема від Contraindications/Diseases: id --
   зовнішній WHO-ідентифікатор (URI/blockId), НЕ синтетичний DB PK,
   на відміну від усіх інших сутностей проекту.
2. Read-only API -- вузли заповнюються importer-ом, немає POST.
3. Явно поза scope: Universal Clinical Classification Layer
   (Second Consumer Rule), живий ICD-API ВООЗ, повне дерево 17000+
   вузлів -- v1 тільки розділ 1.

## Implementation
- `app/modules/icd11/domain/entities.py` -- `ICD11Node`
  (id, parent_id, icd_code, english_title, ukrainian_title,
  translation_status, node_kind, special_code, sort_order,
  source_release), `TranslationStatus`/`NodeKind`/`SpecialCode` enum,
  валідація: тільки `id` не порожній (жорстко); зв'язок
  node_kind/icd_code -- документований, не enforced (ADR-0015 п.4).
- `app/modules/icd11/persistence/{orm,mapper,repository}.py` --
  `ICD11NodeORM`, String(500) PK, self-referencing FK `parent_id` ->
  `icd11_nodes.id` (ON DELETE SET NULL), окремі ORM-enum класи
  (той самий підхід, що `InteractionSeverityORM` у Drug Interactions).
  `get_children(parent_id)`, `get_all()` (сортування за sort_order).
- `app/modules/icd11/schemas/icd11.py` -- лише `ICD11NodeRead`, немає
  Create-схеми (read-only knowledge asset).
- `app/modules/icd11/application/service.py` -- `ICD11Service.get_node()`,
  `list_children()`.
- `app/modules/icd11/api/routes.py` -- `GET /icd11/nodes` (без
  parent_id -- корені; з parent_id -- діти), `GET /icd11/nodes/{node_id:path}`
  (`:path`-конвертер, бо id може містити '/' -- WHO URI).
- Зареєстровано: `app/persistence/model_registry.py`,
  `app/api/router.py` (НЕ `api_core`, як явно вимагало завдання).
- `alembic/versions/f2b8d5a1c7e3_add_icd11_nodes_table.py` --
  `down_revision='a7d4f1c9b3e6'`.
- `tests/modules/icd11/test_entities.py` -- 9 тестів.
- `tests/modules/icd11/test_persistence.py` -- 4 тести (roundtrip,
  self-referencing parent x2, get_all сортування).

## Verification
Sandbox: 13/13 pytest (domain + persistence). Додатково --
`TestClient` smoke (не закомічено як постійний тест, той самий підхід,
що Diseases Live API Verification, S06E02): GET /icd11/nodes (корені)
200, GET /icd11/nodes?parent_id=... (діти) 200, GET /icd11/nodes/{id}
200, GET /icd11/nodes/неіснуючий 404, і окремо -- id з реальним WHO
URI (`http://id.who.int/icd/release/11/2024-01/mms/123`, містить '/')
коректно оброблено через `{node_id:path}` -- 200.

Реальний venv -- очікування нижче, ще НЕ підтверджено користувачем.

## Продовження (importer + seed, після отримання реального файлу)
Джерело: `SimpleTabulation-ICD-11-MMS-en.xlsx` (офіційний ВООЗ,
icdcdn.who.int, ~36044 рядків), `D:\FHOS\external_data\icd11\`.

- `app/modules/icd11/persistence/who_source_loader.py` --
  `load_icd11_chapter_from_xlsx()`: двопрохідна побудова parent_id
  через BlockId/Grouping1-5, фільтр за ChapterNo (застосовується
  ПІСЛЯ побудови BlockId->URI мапи, не до), парсинг special_code із
  суфіксу Code, очищення title від маркера вкладеності. Друкує
  діагностику при кожному запуску (заголовок файлу, кількість
  листів, знайдена/не знайдена колонка версії, лічильники skip) --
  той самий підхід, що `medic_source_loader.py`.
- `scripts/seed_icd11_data.py` -- ідемпотентний (дедуплікація за
  `id` напряму, це реальний PK), `flush()` після кожного вузла --
  явний порядок insert для self-referencing FK (ORM не оголошує
  `relationship()` для parent_id, тож SQLAlchemy unit-of-work не має
  автоматичної інформації про залежність дитина/батько).
- `tests/modules/icd11/test_who_source_loader.py` -- 9 тестів на
  синтетичному xlsx (не реальний файл -- тести детерміновані,
  не залежать від зовнішнього джерела): фільтр глави, невідомий
  ClassKind, parent resolution (включно з точним випадком із
  завдання: 1A03.0 -> Code=1A03), special_code, очищення title,
  колонка версії.
- `requirements.txt` -- додано `openpyxl==3.1.5`.

### Verification
Sandbox: 9/9 pytest на синтетичних даних, що повторюють реальну схему
(18 колонок, Grouping1-5, непередбачувана назва колонки версії).
Окремо -- ручна перевірка через `load_icd11_chapter_from_xlsx()` +
друк результату: усі очікувані поля (parent_id, special_code, title
без маркера) підтверджені візуально. Seed-скрипт: idempotency
підтверджена (2 прогони, другий -- 0 додано, 5 дублікат).

Реальний venv, підтверджено користувачем 2026-07-09:
- `pytest tests/modules/icd11/ -v` -- 22/22 passed.
- `pytest tests/ -v` -- 206/206 passed.
- `alembic upgrade head` / `alembic current` -- `f2b8d5a1c7e3` (head).
- `python scripts/seed_icd11_data.py` (1-й прогін) -- заголовок
  файлу 19 колонок (реальний файл має одну зайву безіменну колонку
  після Version -- importer обробив коректно завдяки захисному
  `dict(zip(header, values))`), 36044 рядків даних, BlockId->URI мапа
  726 записів, розділ 01: **1055 вузлів імпортовано**, 34989 інших
  глав, 0 невідомих ClassKind, 0 невалідних, 0 нерозв'язаних parent.
- `python scripts/seed_icd11_data.py` (2-й прогін) -- 0 додано, 1055
  пропущено як дублікат (ідемпотентність підтверджена).
- `python -c "from app.main import app"` -- без помилок.
- Попередження про кілька листів у файлі НЕ з'явилось -- файл
  однолистовий.

## Ліцензування ICD-11 (виправлено після прямої перевірки)
Початкове формулювання завдання називало ліцензію "CC BY-NC-ND".
Перевірено напряму на https://icd.who.int/docs/icd-api/license/ --
насправді **CC BY-ND 3.0 IGO** (Attribution-NoDerivs, БЕЗ компонента
NonCommercial). Немає обмеження на комерційне використання; заборонені
"adaptations" (похідні роботи) класифікації як такої; копіювання й
поширення дозволені за умови коректної атрибуції. Зафіксовано в
ADR-0015 і PROJECT_STATE.md.

## Явно НЕ зроблено
Немає -- модуль завершено в межах узгодженого v1 scope (ADR-0015).
Наступний крок -- окреме рішення поза цим спринтом, чи звіряти
Diseases.icd_code проти дерева ICD11Node (Second Consumer, не
зроблено мовчки).
