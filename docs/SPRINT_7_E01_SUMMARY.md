# Sprint 7 E01 -- Contraindications v1: Architect Session + Domain Layer

## Architect Session
Рішення користувача (зафіксовані до коду):
1. Асиметрична модель (substance_chebi_id / disease_mondo_id), без pair_key().
2. Без severity -- MeDIC v1 не надає цих даних.
3. CHEBI / MONDO як ідентифікатори.
4. v1 не будує active_substances/clinical_moieties для 3857 препаратів
   MeDIC -- окреме, велике рішення, відкладено.

Контрзауваження (Devil Review), прийняте як робоче припущення:
відкладений мапінг стосується ОБОХ боків симетрично --
Medications.drug_name -> CHEBI і Diseases.diagnosis_name -> MONDO
однаково не розв'язані. Domain-шар цього не потребує; Application-шар
буде заблокований, поки один із двох мапінгів не з'явиться.

Деталі -- docs/ADR/ADR-0014-contraindications-v1-domain-scope.md.

## Implementation (тільки domain-шар)
- `app/modules/contraindications/domain/entities.py`:
  `Contraindication` (substance_chebi_id, disease_mondo_id, description,
  knowledge_source_id, id), валідація CHEBI:/MONDO: префіксів у
  `__post_init__`, `matches()`, модульна функція `find_contraindications()`.
- `tests/modules/contraindications/test_entities.py`: 13 тестів
  (TestValidation x6, TestMatches x4, TestFindContraindications x3).

## Data profiling (MeDIC Contraindications List.csv)
Реальний файл, профільовано напряму (діагностичний скрипт
`diagnose_medic_missing_ids.py`, одноразовий, НЕ закомічений):
7962 рядки всього.
- 1197 (15%) -- CHEBI+MONDO, висока довіра LLM -- завантажено.
- 619 (8%) -- CHEBI+MONDO, але llm_nameres_correct/_drug=FALSE --
  відкинуто фільтром довіри.
- 2165 (27%) -- розпізнані, але в інших словниках: RXCUI (884),
  PUBCHEM.COMPOUND (367), UNII (216), DRUGBANK (132), MESH (34),
  CHEMBL.COMPOUND (2) для речовин; MONDO присутній лише частково --
  UMLS (379), HP (376, фенотипи, не хвороби), NCIT (27), EFO (14),
  DOID (4) для хвороб.
- 3981 (50%) -- обидва боки повністю нерозпізнані джерелом.

Рішення користувача (Architect Session, 2026-07-09): залишити v1
обсяг без змін -- тільки CHEBI/MONDO, 1197 записів. Розширення
словників відхилено як Confirmed Intention без жодного реального
випадку "бракує запису" (не Confirmed Repetition). DOID->MONDO міст
(4 рядки) також відхилено -- замалий приріст, щоб виправдати окремий
крок мапінгу. Це узгоджується з ADR-0014 п.3 (CHEBI/MONDO -- єдині
канонічні ідентифікатори v1) та окремим Architecture Review про Drug
Identity Model (де інші namespace мапляться в CHEBI лише через
майбутню точку розширення `clinical_moieties`, не приймаються напряму
в domain-модель).

## Persistence + seed
- `app/modules/contraindications/persistence/{orm,mapper,repository}.py`
  -- `ContraindicationORM`, без DB-рівня UNIQUE (дедуплікація на рівні
  seed-скрипта, як у Drug Interactions), композитний індекс
  `ix_contraindications_substance_disease`.
- `alembic/versions/a7d4f1c9b3e6_add_contraindications_table.py` --
  `down_revision='e4f6a8c1d3b5'`.
- `scripts/seed_medic_data.py` -- ідемпотентний, дедуплікація за
  `(substance_chebi_id, disease_mondo_id)` (не pair_key() -- асиметрична
  модель).
- `app/modules/contraindications/persistence/medic_source_loader.py` --
  читання CSV, MEDIC_DATA_DIR env var, фільтри CHEBI:/MONDO: +
  llm_nameres_correct.

## Verification
Sandbox: логіка завантажувача і seed-скрипта перевірена на синтетичних
даних (включно з edge case -- багаторядкове quoted-поле в CSV),
ідемпотентність підтверджена (другий прогін: 0 додано).

Реальний venv, підтверджено користувачем 2026-07-09:
- `pytest tests/modules/contraindications/ -v` -- 16/16 passed
  (13 domain + 3 persistence).
- `pytest tests/ -v` -- 184/184 passed.
- `alembic upgrade head` -- e4f6a8c1d3b5 -> a7d4f1c9b3e6.
- `alembic current` -- a7d4f1c9b3e6 (head).
- `python scripts/seed_medic_data.py` (1-й прогін) -- 1197 додано.
- `python scripts/seed_medic_data.py` (2-й прогін) -- 0 додано,
  1197 пропущено як дублікат (ідемпотентність підтверджена).

## Явно НЕ зроблено (наступні кроки, не блокери)
- application/service.py -- не написаний (заблокований мапінгом,
  див. ADR-0014 п.4: Medications.drug_name->CHEBI або
  Diseases.diagnosis_name->MONDO, жодне не розв'язане).
- api/routes.py -- не написаний.
- Розширення словників (RxNorm/PubChem/UNII/DrugBank, UMLS/DOID) --
  свідомо відхилено на цьому кроці, не забуто (див. Data profiling
  вище).
- `diagnose_medic_missing_ids.py` -- одноразовий діагностичний
  скрипт, аналогічний `verify_diseases_live.py` (S06E02). НЕ
  призначений для коміту -- рішення видалити чи залишити за
  користувачем перед `git add`.
