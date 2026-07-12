# S08E01 — Clinical Reasoning Graph Persistence + Family Data Access

## Реалізовано

- Persistence для `HealthNode`, `HealthRelation`, `ClinicalHypothesis`, `PatientNodeState`.
- `ConsentEnvelope` з purpose-bound scope, операціями, resource selectors і disclosure level.
- `GuardianAuthority` з deny-by-default та перевіреним строком дії.
- `JurisdictionPolicy` як версійована структура, а не глобальна константа віку.
- `CareTransitionEvent` як доменна подія без автоматичного розширення доступу.
- `FamilyAccessDecision`.
- Авторизована проєкція спільних вузлів.
- API для створення/відкликання згоди та отримання дозволених shared nodes.
- `REVOKED` без фізичного видалення audit-запису.
- Alembic revision `c8e1f4a9b2d7`, down_revision `f2b8d5a1c7e3`.

## Перевірка

- Усі тести: `280 passed`.
- Alembic upgrade на копії `fhos_local.db`: успішно.
- Поточний Alembic head: `c8e1f4a9b2d7`.

## Критичний E2E-сценарій

1. Чоловік запитує shared nodes із дружиною без згоди — результат порожній.
2. Дружина дає consent лише на `MONDO:STAPH`, purpose `shared_infection_assessment`, operation `compare`.
3. Shared node стає доступним лише в дозволеному scope.
4. Consent переходить у `REVOKED`.
5. Повторний запит знову повертає порожній результат.
6. Запис згоди та `revoked_at` залишаються в БД.

## Команди після заміни backend

```powershell
cd D:\FHOS\FHOS_v0.1_MVP\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
pytest -q
uvicorn app.main:app --reload
```

## Нові API

- `POST /api/clinical-reasoning/family-consents`
- `POST /api/clinical-reasoning/family-consents/{consent_id}/revoke`
- `POST /api/clinical-reasoning/family/shared-nodes`

## Обмеження MVP

- `JurisdictionPolicy` має структуру і persistence, але юридичний довідник країн ще не наповнений.
- Care Transition має persistence, але scheduler/notifications ще не реалізовані.
- Guardian restrictions зараз трактуються як перелік заборонених operations; складні категорії конфіденційної допомоги залишаються наступним епізодом.
