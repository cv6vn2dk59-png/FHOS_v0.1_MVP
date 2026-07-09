# Sprint 7 E03 -- Substance Name -> CHEBI mapping (ADR-0012 завершення)

## Контекст
ADR-0012 явно передбачив цей момент: "як тільки з'явиться другий
реальний споживач -- виносити мапінг в окремий компонент". Contraindications
(CHEBI-based, ADR-0014) -- цей другий споживач.

## Implementation
- `app/shared/drug_identity/__init__.py`, `substance_mapping.py` --
  `BRAND_TO_SUBSTANCE` перенесено як є з
  `drug_interactions/domain/name_mapping.py`. Новий шар
  `SUBSTANCE_TO_CHEBI` + `normalize_to_chebi()`.
- `app/modules/drug_interactions/domain/name_mapping.py` --
  `BRAND_TO_SUBSTANCE` тепер імпортується з shared-модуля (single
  source of truth), `normalize_drug_name()` лишився тут (domain-
  специфічна операція, не загальна утиліта).
- `scripts/build_substance_to_chebi.py` -- документує й відтворює
  точний алгоритм резолюції (exact-token-match на `drug_name`,
  перший `CHEBI:`-рядок серед точних збігів).
- `tests/shared/drug_identity/test_substance_mapping.py` -- 10
  тестів: усі 4 речовини (пряма назва + українська брендова назва),
  unknown -> None, узгодженість словників.

## Реальні значення (MeDIC Drug List.csv, перевірено напряму через
Grep на реальному файлі, S07E03)
- warfarin -> CHEBI:10033
- amiodarone -> CHEBI:2663
- sertraline -> CHEBI:9123
- tranylcypromine -> CHEBI:9653 (сіль-форма, явне рішення -- див. нижче)

## Знахідка: tranylcypromine -- виняток з базового алгоритму
Точний токен-збіг "tranylcypromine" у `drug_name` веде на
`PUBCHEM.COMPOUND:73417116` (НЕ CHEBI). Єдиний CHEBI-рядок --
`CHEBI:9653`, `drug_name="TRANYLCYPROMINE SULPHATE"` -- сіль-форма,
яка НЕ проходить точний токен-збіг за описаним алгоритмом. Це не
гіпотетичний край випадок: tranylcypromine -- MAOI в парі MAOI-SSRI
з датасету Phansalkar (Drug Interactions v1), одна з
найважливіших взаємодій, які Contraindications мав би покривати.

Рішення НЕ прийнято мовчки автоматичним "найближчим збігом" --
`scripts/build_substance_to_chebi.py` для цього випадку явно друкує
попередження й лишає `None`. Користувач підтвердив явно (S07E03):
прийняти CHEBI:9653 як еквівалент -- та сама речовина, інших
CHEBI-варіантів немає. Зафіксовано в коді (docstring
`substance_mapping.py`) і в ADR-0012 (розділ "Оновлення").

## Verification
Sandbox: 10/10 pytest на реальних значеннях (не синтетичних --
самі CHEBI-константи перевірені напряму на реальному
`MeDIC Drug List.csv` через Grep перед записом у код). Регресія
Drug Interactions підтверджена окремо: `normalize_drug_name()`
дає ідентичний результат після зміни джерела `BRAND_TO_SUBSTANCE`
(кордарон -> amiodarone, варфарин -> warfarin, unknown passthrough).

Реальний venv -- команди нижче, ще не підтверджено користувачем.
