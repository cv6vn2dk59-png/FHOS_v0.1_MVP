# Sprint 7 E05 -- Contraindications v1: application-шар + API (ADR-0014, закриття)

## Контекст
S07E03 (Substance→CHEBI) і S07E04 (Diseases→MONDO) закрили обидва
боки мапінгу, необхідні за ADR-0014 п.4. Цей епізод -- останній крок:
Application-шар і API, що читають Medications/Diseases пацієнта і
шукають відомі протипоказання.

## Implementation
- `app/modules/contraindications/application/service.py` --
  `ContraindicationService.check_patient(patient_profile_id)`:
  читає АКТИВНІ (`is_active()==True`) `Medications` і `Diseases`
  пацієнта через `MedicationService`/`DiseaseService`, нормалізує
  `drug_name` через `normalize_to_chebi()` (shared, S07E03) і
  `diagnosis_name` через `normalize_to_mondo()` (local, S07E04),
  шукає збіги через `find_contraindications()` (domain, ADR-0014).
  Записи без збігу в словнику (`None` від normalize_*) мовчки
  відкидаються -- не fuzzy-match, не вигадування відповідності.
- `app/modules/contraindications/schemas/contraindications.py` --
  `ContraindicationRead` (read-only, немає Create -- knowledge asset
  із seed, той самий підхід, що `ICD11NodeRead`).
- `app/modules/contraindications/api/routes.py` --
  `GET /contraindications/patient/{patient_profile_id}`, зареєстровано
  в `app/api/router.py`.
- `tests/modules/contraindications/test_service.py` -- 8 тестів:
  знаходить протипоказання (активний препарат + активна хвороба),
  нормалізує українську брендову назву й альтернативну форму запису
  хвороби (гіпертонія / артеріальна гіпертензія -- обидві на
  MONDO:0005044), ігнорує неактивний препарат, вирішену хворобу,
  препарат/діагноз поза стартовими словниками, порожній результат при
  відсутності даних пацієнта. `CHEBI:10033`/`MONDO:0005044` у тестах
  -- вигаданий тестовий Contraindication-фікстур (той самий підхід,
  що вже в `test_persistence.py` з metformin), НЕ реальний клінічний
  факт з MeDIC.

## Свідомо задокументована поведінкова межа
`normalize_to_chebi()`/`normalize_to_mondo()` -- exact-match проти
навмисно малих словників (4 речовини, 10 хвороб). Порожній результат
`check_patient()` НЕ означає "протипоказань немає" -- здебільшого
означає "жоден препарат/діагноз пацієнта не потрапив у ці малі
словники". Задокументовано в docstring сервісу, docstring API route
і ADR-0014 (оновлення S07E05) -- у трьох місцях свідомо, не залишено
лише в коді.

## Verification
Sandbox: 8/8 pytest (`test_service.py`, in-memory SQLite,
foreign_keys=ON). API-шар -- окремий smoke-тест через
`TestClient` (StaticPool sqlite, бо звичайний `:memory:` без
StaticPool дає кожному з'єднанню окрему порожню БД -- артефакт
пісочниці, не реального PostgreSQL-застосунку): `GET
/contraindications/patient/1` -> `200`, `[]`. Формального
TestClient-тесту в постійному наборі не додано (відкритий
project-wide backlog-пункт, не локальне рішення).

Реальний venv -- команди нижче, ще не підтверджено користувачем.
