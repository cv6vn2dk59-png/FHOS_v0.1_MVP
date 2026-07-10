# Sprint 7, Episode 07 — Devil Review remediation

## Контекст
Перед комітом S07E05 (Contraindications application-шар) + S07E06
(ICD-11 повне дерево) власник попросив звіт "як програмист, для
диявола" — структурований Devil Review за skill `devils-advocate-
reviewer`. Знайдено кілька ризиків; власник погодив 4 конкретні кроки
ремедіації, у визначеному порядку, явно відхиливши частину моїх
пропозицій.

## Погоджені кроки (порядок власника)

### 1. Реальний E2E-тест на 1197 записах
Найбільша прогалина: усі 8 тестів `test_service.py` (S07E05) — на
вигаданій парі `CHEBI:10033`/`MONDO:0005044`, жоден ланцюжок ніколи
не прогнаний на реальних seed-даних.

Незалежно перевірено напряму на CSV (`Contraindications List.csv`,
рядки 2642, 6548), потім підтверджено реальним запуском у venv
власника:

```
кордарон (укр. бренд) -> BRAND_TO_SUBSTANCE -> amiodarone
  -> SUBSTANCE_TO_CHEBI -> CHEBI:2663
кардіогенний шок -> DISEASE_TO_MONDO -> MONDO:0800175

check_patient() -> 1 знайдено: CHEBI:2663 + MONDO:0800175,
  "Amiodarone is contraindicated in patients with cardiogenic
  shock, severe sinus-node dysfunction..." (реальний опис MeDIC,
  рядок 2642)
```

Перший прогін скрипта впав із `NoReferencedTableError` — скрипт не
імпортував `app.modules.profile.persistence.orm`, тому `patient_
profiles` не потрапила в `Base.metadata` до flush `MedicationORM`
(FK). Виправлено додаванням `import app.persistence.model_registry`
першим рядком скрипта. Це моя помилка в скрипті, не проблема бази чи
проєкту.

Повний ланцюжок (укр. вільний текст → нормалізація → CHEBI/MONDO →
пошук серед реальних записів → реальний опис) тепер підтверджений на
реальних даних, не лише на фікстурах. Деталі також у ADR-0014,
"Оновлення (S07E07)".

### 2. `raise` замість `print` для unresolved_parents
`ICD11Node.is_root()` перевіряє лише `parent_id is None` — вузол-
сирота (Grouping-посилання на неіснуючий BlockId) виглядав би
невідрізнюваним від справжнього кореня глави. Раніше
`load_icd11_chapter_from_xlsx()` лише друкував попередження.

Змінено: `unresolved_parents > 0` тепер кидає `ValueError` з
кількістю та контекстом (`app/modules/icd11/persistence/
who_source_loader.py`).

Додано `TestUnresolvedParentRaises` (2 тести, синтетичний фікстур із
гарантовано нерозв'язаним `Grouping1="ghost-block"`).

Цей `raise` одразу зловив реальний, раніше непомічений баг у власній
тестовій фікстурі S07E06: рядок `who:category-2A00` (глава 02, Grouping1
= "2") не мав відповідного кореня `BlockId="2"` ніде у фікстурі —
раніше невидимо, бо тести з фільтром по главі (`chapter_no="01"`)
ніколи не резолвили батька цього рядка. Виправлено додаванням
правильного кореневого рядка `who:chapter-02`; оновлено
`test_count_equals_all_valid_rows_regardless_of_chapter` (6 → 7),
додано `test_chapter_02_category_parent_resolves_correctly`.

Це підтверджує цінність зміни: перетворює тихе спотворення дерева на
негайний, гучний фейл — і одразу довело це на власному прикладі.

Пісочниця: 16/16 (`tests/modules/icd11/test_who_source_loader.py`).
Реальний venv, підтверджено власником: **248/248** (245 + 3 нових).

### 3. `coverage_warning` — статичне текстове поле
Найважливіший клінічний ризик Devil Review: порожній результат
`GET /contraindications/patient/{id}` виглядає як "протипоказань
немає", а насправді здебільшого означає "жоден препарат/діагноз
пацієнта не потрапив у малі стартові словники" (4 речовини CHEBI, 10
хвороб MONDO).

Я запропонував динамічні лічильники (`unmapped_medications_count`,
`unmapped_diseases_count`) — власник явно відхилив це як розширення
Scope ("нова структура даних, нова логіка підрахунку") і обрав
простіший варіант.

Реалізовано: відповідь API стала об'єктом, не голим списком —

```json
{
  "contraindications": [...],
  "coverage_warning": "Перевірка обмежена малими словниками (CHEBI: 4 речовини, MONDO: 10 хвороб). Порожній результат НЕ означає відсутність протипоказань -- препарат або діагноз пацієнта міг не потрапити в жоден зі словників."
}
```

`coverage_warning` — константа, ідентична завжди (порожній чи
непорожній результат), без підрахунку. Domain/application-шар
(`ContraindicationService.check_patient()`) не змінено — і далі
повертає `list[Contraindication]`; обгортку (`ContraindicationCheckResult`)
будує лише route-шар. Перевірено ізольовано в пісочниці (pydantic
`model_dump_json()` на порожньому й непорожньому випадку — текст
попередження ідентичний в обох).

Формального TestClient-тесту не додано — той самий project-wide
backlog-пункт "API-рівня тести відсутні як постійний шар"
(PROJECT_STATE.md), не рішення цього кроку (додавання нової тестової
інфраструктури не входило в 4 погоджені кроки).

### 4. `is_active()` — залишено ВІДКРИТИМ
Я підняв як приховане припущення: чи "активний сьогодні" — правильне
клінічне вікно релевантності для Contraindications (деякі
протипоказання релишаються релевантними і після завершення прийому чи
формального "resolved" діагнозу)? Це той самий фільтр, що
`DrugInteractionService.check_active_medications()`.

Власник явно відмовився вирішувати це одноосібно чи мовчки
успадковувати існуючий патерн — питання вимагає або медичної
експертизи, або явного product-owner-рішення. Задокументовано як
відкритий пункт backlog у PROJECT_STATE.md ("ВІДКРИТЕ клінічне
питання, СВІДОМО не вирішене"), не вирішено мовчки.

## Підсумок тестів
- Крок 1: 0 нових тестів (незалежна верифікація на реальних даних,
  не нова тестова інфраструктура).
- Крок 2: +3 тести (248/248 підтверджено користувачем у реальному
  venv).
- Крок 3: 0 нових тестів (свідомо — формальний API-тест поза межами
  4 погоджених кроків).
- Крок 4: 0 нових тестів (документація).

## Файли
- `app/modules/icd11/persistence/who_source_loader.py` — `raise`.
- `tests/modules/icd11/test_who_source_loader.py` — `TestUnresolvedParentRaises`,
  фікс власного багу в `TestFullTreeNoChapterFilter`.
- `app/modules/contraindications/schemas/contraindications.py` —
  `ContraindicationCheckResult`, `COVERAGE_WARNING`.
- `app/modules/contraindications/api/routes.py` — response_model
  змінено на `ContraindicationCheckResult`.
- `docs/ADR/ADR-0014-contraindications-v1-domain-scope.md` — оновлення
  кроку 3.
- `docs/PROJECT_STATE.md` — відкритий backlog-пункт `is_active()`,
  запис "Наступна робота".
