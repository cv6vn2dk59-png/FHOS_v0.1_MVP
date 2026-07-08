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
  Alembic head: 9a3d7c1f2b6e.

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

## Відкритий backlog (не блокери)
- LaboratoryRepository.get_latest_result() — unused, рішення не прийнято
  (використати чи видалити)
- LaboratoryResultCreate.validate_reference_range() — навмисне дублювання
  domain-інваріанту (fail-fast на межі API), потребує явного коментаря в коді

## Наступна робота
- Seed script для реальних 15 записів Phansalkar 2013 у таблицю
  drug_interactions (fallback на дані в пам'яті досі покриває
  функціональність v1, не блокер).
- Consistency Review Drug Interactions (за зразком Laboratory) — після
  накопичення досвіду використання усіх трьох блоків Evidence View.
- Прогнати повний `python -m pytest tests/ -v` у робочому venv проєкту
  для patient_note (перевірено лише на мінімальній копії зачеплених
  файлів у чистому середовищі — див. docs/SPRINT_5_E02_SUMMARY.md).
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
