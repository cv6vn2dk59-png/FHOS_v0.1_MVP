@'
# FHOS — Project State Snapshot

Останнє оновлення: Sprint 4, ADR Consolidation (2026-07-05/06)

## Constitution
Поточна версія: v3.1
Canonical метод: abnormality_score() (не risk_score() — видалено, ADR-0010)

## Завершені модулі
- Laboratory (vertical slice): interpret(), is_out_of_range(), trend(),
  abnormality_score(), deviation_percent()
- Reference Range Resolver v1 (ADR-0004, ADR-0005, ADR-0007)
- Imaging v1
- Medications v1 (ADR-0009) — commit 32e7995
- Trend Risk v1 (ADR-0011) — TrendAnalysisService.assess_trend_risk(),
  API: GET /laboratory/patient/{id}/trend-risk/{test_code}
  — commits 8706d3d, a38064f
- Drug Interactions v1 (Sprint 5, docs/SPRINT_5_E01_SUMMARY.md,
  docs/SPRINT_5_E02_SUMMARY.md) — Interaction Evidence View завершено,
  усі три блоки: verified_interaction, prescription_history, patient_note.
- Diseases v1 (ADR-0013, docs/SPRINT_6_E01_SUMMARY.md,
  docs/SPRINT_6_E02_SUMMARY.md, дзеркально до Medications v1/ADR-0009) —
  Disease.is_active()/duration_days() через resolved_date (nullable,
  без третього статусу), diagnosis_name вільний текст + опціональний
  icd_code, без cross-module залежностей. API: POST /diseases/,
  GET /diseases/patient/{id}. Alembic head: e4f6a8c1d3b5. Live API
  Verification і Consistency Review виконано (S06E02) — 168/168
  підтверджено користувачем у реальному venv 2026-07-08.
- Contraindications v1 — ТІЛЬКИ domain-шар (ADR-0014,
  docs/SPRINT_7_E01_SUMMARY.md): Contraindication (substance_chebi_id,
  disease_mondo_id, description, knowledge_source_id), асиметрична
  модель, без pair_key(), без severity (MeDIC v1 не надає). CHEBI/MONDO
  як ідентифікатори, без FK на ще не існуючу active_substances
  таблицю (той самий підхід, що name_mapping.py в Drug Interactions).
  persistence/application/API — НЕ написані, заблоковано рішенням про
  Medications.drug_name→CHEBI або Diseases.diagnosis_name→MONDO мапінг
  (жодне ще не прийнято). 13 нових тестів, підтвердження в реальному
  venv — див. "Наступна робота".

## Governance
Architecture Governance Lifecycle: ADR-0008 (актуальна версія, supersedes ADR-0006)
Discussion → Architecture Decision → Implementation → Validation →
Retrospective/Devil Review → ADR → Constitution Update → Approved Architecture

## Технічна інфраструктура
- .gitattributes додано (commit 2a811bb) — LF для .py/.md/.json/etc, CRLF для .ps1/.bat
- PostgreSQL Compatibility Checklist: docs/DEVELOPER_GUIDE/

## ADR (актуальний список)
- ADR-0001 — data owner
- ADR-0002 — ukrainian-first
- ADR-0003 — platform independent
- ADR-0004 — Reference Range як Knowledge Asset
- ADR-0005 — Reference Range Resolver specificity
- ADR-0006 — Governance Lifecycle (Superseded by ADR-0008)
- ADR-0007 — Specificity score = deterministic ordering, not clinical priority
- ADR-0008 — Governance Lifecycle v2 (актуальний)
- ADR-0009 — Medications v1 Domain Scope
- ADR-0010 — abnormality_score() Rename Completed
- ADR-0011 — Trend Risk v1: deviation_percent() basis
- ADR-0012 — Medication name mapping lives in Drug Interactions
- ADR-0013 — Diseases v1 Domain Scope
- ADR-0014 — Contraindications v1 Domain Scope (тільки domain-шар)

## Відкритий backlog (не блокери)
- LaboratoryRepository.get_latest_result() — unused, рішення не прийнято
  (використати чи видалити)
- LaboratoryResultCreate.validate_reference_range() — навмисне дублювання
  domain-інваріанту (fail-fast на межі API), потребує явного коментаря в коді
- PatientInteractionNote.pair_key() — unused поза тестами (той самий
  патерн, що LaboratoryRepository.get_latest_result() вище), рішення
  не прийнято (docs/SPRINT_5_E03_SUMMARY.md)
- Optional-типізація patient_profile_id неоднорідна в межах
  DrugInteractionService (і ширше — у Medications) — існуюча конвенція
  проєкту, не локальна помилка, потребує рішення на рівні проєкту, не
  одного модуля
- drug_interactions/domain/entities.py росте (4 domain-об'єкти в одному
  файлі) — кандидат на розділення, поки не блокер
- Diseases diagnosis_name — вільний текст без жодного name_mapping-
  подібного компонента (на відміну від Medications/ADR-0012) — ризик
  для майбутньої Contraindications Architect Session, не помилка v1
  (docs/SPRINT_6_E02_SUMMARY.md, Devil Review п.3)
- API-рівня (TestClient) тести відсутні як постійний шар у жодному
  модулі проєкту — Testing Guide їх не описує; рішення чи вводити цей
  шар офіційно не прийнято (docs/SPRINT_6_E02_SUMMARY.md, п.4)
- MedicationCreate.validate_dates() досі без явного коментаря про
  навмисне дублювання domain-інваріанту (DiseaseCreate вже отримав
  такий коментар, Medications — ні, project-wide, не Diseases-локально)
- Contraindications v1 application/API-шар заблокований: потрібне
  рішення про мапінг Medications.drug_name→CHEBI АБО
  Diseases.diagnosis_name→MONDO (хоча б один бік) — окремий Architect
  Session, не зроблено мовчки (ADR-0014, docs/SPRINT_7_E01_SUMMARY.md)

## Наступна робота
- Seed script (Drug Interactions) і Consistency Review — ЗРОБЛЕНО і
  ПІДТВЕРДЖЕНО користувачем у реальному venv 2026-07-08: git status,
  alembic current (9a3d7c1f2b6e на той момент), pytest 147/147, потім
  150/150 після нормалізації substance_a/substance_b. Деталі —
  docs/SPRINT_5_E03_SUMMARY.md.
- Diseases v1 (ADR-0013) — ЗРОБЛЕНО і ПІДТВЕРДЖЕНО користувачем у
  реальному venv 2026-07-08: alembic upgrade head → e4f6a8c1d3b5,
  pytest 165/165.
- Live API Verification + Consistency Review Diseases v1 (S06E02) —
  ЗРОБЛЕНО (ця сесія): 8/8 сценаріїв через реальний TestClient (create/
  minimal/invalid patient/422 на кількох межах), 2 виправлення внесено
  (коментар до дублювання валідації, 3 нових тести
  `TestSchemaValidation`), 3 пункти винесено в backlog вище (Devil
  Review про diagnosis_name normalization, API-testing strategy,
  MedicationCreate без коментаря). Підтверджено лише в ізольованому
  середовищі — НЕ у вашому venv. Перед комітом прогнати:
  ```powershell
  cd D:\FHOS\FHOS_v0.1_MVP\backend
  python -m pytest tests/ -v
  ```
  Очікування: 165 (попередніх) + 3 нових = 168 passed.
- Contraindications v1 domain-шар (S07E01) — ЗРОБЛЕНО (ця сесія),
  файли записані напряму у проєкт (відкритий доступ до теки), ще НЕ
  підтверджено у вашому venv. Перед комітом прогнати:
  ```powershell
  cd D:\FHOS\FHOS_v0.1_MVP\backend
  python -m pytest tests/modules/contraindications/ -v
  python -m pytest tests/ -v
  git status
  ```
  Очікування: 13/13 нових, 181/181 (168 + 13) загалом. Наступний крок
  ПІСЛЯ підтвердження — окреме рішення, який бік мапінгу (substance→
  CHEBI чи disease→MONDO) розв'язувати першим; application-шар не
  писати до цього рішення.
- Candidate principle (ще не в Constitution): "Confirmed Repetition, not
  Confirmed Intention" — абстракція виправдана лише реальним повторенням,
  що вже відбулося, не впевненістю в майбутньому повторенні. Виникло під
  час обговорення Knowledge Asset Framework — framework відкладено до
  появи другого реального Knowledge Asset (після Drug Interactions).

## Практична нотатка для нових сесій
На початку нової сесії подавати документи в порядку:
PROJECT_STATE.md → CONSTITUTION.md → поточне завдання.
Якщо вставлений текст Constitution відрізняється версією від того, що
зафіксовано вище (v3.1) — довіряти git, не вставленому тексту.
'@ | Set-Content -Path docs\PROJECT_STATE.md -Encoding utf8
## Candidate Principles (обговорення, не Constitution)
Обидва — спостереження з одного Sprint 4, недостатньо підтверджень
(Confirmed Repetition) для формалізації. Переглянути після Drug Interactions.

- **Scope First (евристика Architect Mode, не окремий принцип)**: перед
  проєктуванням архітектури визначити межі предметної області (Scope).
  НЕ те саме, що Confirmed Repetition Before Abstraction — Диявол навів
  валідні контрприклади незалежності цих двох понять (FHIR Import потребує
  Scope без жодного Confirmed Repetition; Repository-абстракція — навпаки).
  Виникло при звуженні Drug Interactions v1 до Drug↔Drug.

- **Devil Advocate потребує окремої цільової функції, не лише ролі**:
  без явної вимоги "спершу знайти й спростувати контрприклад, лише потім
  погоджуватись" роль Devil Advocate вироджується в третього експерта, що
  підтакує. Практичний наслідок для FHOS зараз: у майбутніх Architect
  Sessions (включно з Drug Interactions) явно вимагати від Devil Review
  спершу контрприклад/заперечення, перш ніж приймати пропозицію. Пряме
  застосування до майбутнього Consilium Engine (ADR ще не існує) — Devil
  у консиліумі має окрему цільову функцію, відмінну від "лікарів".
