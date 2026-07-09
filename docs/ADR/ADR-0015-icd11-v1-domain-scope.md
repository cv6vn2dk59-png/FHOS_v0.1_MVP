# ADR-0015: ICD-11 v1 -- Domain Scope

## Статус
Прийнято (Architect Session завершено; domain + persistence +
application + API + importer + seed реалізовано, S07E02, продовження
після отримання реального джерела -- SimpleTabulation-ICD-11-MMS-en.xlsx,
офіційний файл ВООЗ, icdcdn.who.int).

## Контекст
Наступний Knowledge-модуль: статична ієрархія ICD-11 (WHO
Linearization) -- Chapter -> Block -> Category, потрібна як довідник
для майбутнього кодування діагнозів (Diseases.icd_code сьогодні
вільний текст без валідації, ADR-0013).

## Рішення

1. **id -- зовнішній стабільний ідентифікатор, не синтетичний.**
   WHO Linearization URI або blockId, обов'язковий параметр
   конструктора (на відміну від решти сутностей проекту, де
   `id: int | None = None` призначається базою даних). parent_id --
   self-referencing FK на цю ж таблицю.

2. **Без severity/додаткових полів поза специфікацією.** Точний
   набір полів: id, parent_id, icd_code, english_title,
   ukrainian_title, translation_status, node_kind, special_code,
   sort_order, source_release.

3. **Read-only API.** Немає ICD11NodeCreate/POST-ендпоінта -- вузли
   заповнюються importer-ом/seed-скриптом зі статичного джерела, не
   через API. Той самий підхід, що DrugInteraction: knowledge asset
   сам по собі не приймає запис ззовні, лише читається.

4. **Явно поза межами v1:**
   - Universal Clinical Classification Layer -- відхилено (Second
     Consumer Rule: немає другого реального класифікатора в проекті,
     що потребував би спільної абстракції над ICD-11 і, скажімо,
     майбутнім ATC чи LOINC).
   - Живий виклик ICD-API ВООЗ -- не зараз, статичний імпорт з
     підготовленого файлу.
   - Повне дерево 17000+ вузлів -- v1 обмежується тестовою
     підмножиною (розділ 1). Розширення на повне дерево -- окреме
     майбутнє рішення.
   - Валідація зв'язку node_kind/icd_code (чи можуть Block/Chapter
     мати icd_code) -- НЕ жорсткий constraint, лише документована
     форма очікуваних даних. Реальні WHO-дані можуть мати винятки;
     штучна заборона без підтвердженого правила з джерела -- це
     Confirmed Intention, не Confirmed Repetition.

## Importer (розблоковано, S07E02 продовження)
Джерело: `SimpleTabulation-ICD-11-MMS-en.xlsx` (офіційний ВООЗ,
icdcdn.who.int, повна MMS-класифікація, ~36044 рядків). v1 читає
лише `ChapterNo == "01"` -- відповідає п.4 вище.

Побудова дерева -- двопрохідна (файл не містить прямого parent_id):
1. `{BlockId: Linearization URI}` для ВСІХ рядків файлу.
2. Для кожного рядка обраної глави -- останній непорожній серед
   `Grouping5..Grouping1` (найглибший предок спочатку) -- це BlockId
   найближчого батька. Немає жодного заповненого Grouping -- рядок
   глави (Chapter), `parent_id = None`.

`special_code` -- парситься із суфіксу `Code` (`.Y`/`.Z`).
`english_title` -- очищується від провідного текстового маркера
вкладеності (`- `, `- - `, ...), що дублює структурне node_kind/parent_id.
`ukrainian_title` завжди `None` після importer-а, `translation_status`
завжди `MISSING` -- джерело англомовне, переклад -- окремий майбутній крок.

Перевірено на синтетичних даних, що повторюють реальну схему (9 тестів,
`tests/modules/icd11/test_who_source_loader.py`), включно з точним
випадком із завдання: `1A03.0` -> `parent_id` резолвиться на запис
з `Code=1A03`.

## Ліцензування (перевірено, підтверджено реальним запуском)
ICD-11 ліцензується за **CC BY-ND 3.0 IGO** (Creative Commons
Attribution-NoDerivs), НЕ CC BY-NC-ND, як помилково зазначалось у
початковому формулюванні завдання -- перевірено напряму на
https://icd.who.int/docs/icd-api/license/. Немає обмеження на
комерційне використання; заборонені "adaptations" (похідні роботи)
класифікації як такої; копіювання й поширення дозволені за умови
коректної атрибуції ВООЗ. Повний текст:
https://icd.who.int/en/docs/icd11-license.pdf

Файл `SimpleTabulation-ICD-11-MMS-en.xlsx` -- однолистовий,
попередження importer-а про кілька листів не з'явилось при реальному
запуску (2026-07-09) -- окремого ліцензійного листа в самому файлі
немає.

## Verification (реальний venv, підтверджено 2026-07-09)
`pytest` 206/206, `alembic current` -> `f2b8d5a1c7e3`,
`python -c "from app.main import app"` без помилок. Seed на
реальному файлі: 1055 вузлів розділу 1 (з 36044 рядків -- 34989
інших глав, 0 невідомих ClassKind, 0 невалідних, 0 нерозв'язаних
parent), ідемпотентність підтверджена (другий прогін -- 0 додано,
1055 дублікат).

## Наслідки
- Domain/persistence/application/API-шари готові й перевірені
  (sandbox: 13 domain+persistence тестів, TestClient smoke -- 4
  сценарії включно з WHO URI, що містить '/').
- Таблиця `icd11_nodes` порожня до завершення importer-а -- це не
  блокер для коміту поточного шару, оскільки API коректно повертає
  порожні списки/404 на порожній таблиці (перевірено окремо, root
  node без дітей -- `get_children` повертає []).
- Diseases.icd_code лишається вільним текстом (ADR-0013) -- зв'язок
  Diseases <-> ICD11Node (валідація icd_code проти дерева) НЕ частина
  цього рішення, окреме майбутнє рішення (той самий Second Consumer
  принцип, що і в Contraindications ADR-0014 щодо мапінгу).
