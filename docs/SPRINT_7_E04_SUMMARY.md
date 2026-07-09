# Sprint 7 E04 -- Diseases.diagnosis_name -> MONDO стартовий словник

## Контекст
ADR-0014 п.4: Application-шар Contraindications заблокований, поки
хоч один бік мапінгу (Medications->CHEBI або Diseases->MONDO) не буде
розв'язаний. S07E03 закрив першу половину (Substance->CHEBI). Цей
епізод -- друга половина.

Структурна відмінність від S07E03, названа явно перед стартом: для
Diseases немає готового стартового словника (як BRAND_TO_SUBSTANCE) і
немає реальних пацієнтських Disease-записів для перевірки -- лише
тестові фікстури. Український переклад MONDO-термінів не фабрикується
автором коду (та сама дисципліна, що вже застосована до ICD-11).

## Дані (перевірено напряму, реальний venv, S07E04)
- Реальний файл: `Contraindications List.csv` (MeDIC).
- Унікальних MONDO ID (`final normalized disease id`, будь-який
  рядок): 545.
- Унікальних MONDO ID серед 1197 завантажених записів (фільтр
  CHEBI+MONDO+high LLM confidence -- той самий, що дає 1197): 374.
- Топ-10 за частотою серед цих 374 (MONDO ID / частота / англ. назва
  з MeDIC):
  1. MONDO:0004979 / 69 / asthma
  2. MONDO:0005252 / 28 / heart failure
  3. MONDO:0005068 / 27 / myocardial infarction
  4. MONDO:0002476 / 26 / anuria
  5. MONDO:0800175 / 24 / cardiogenic shock
  6. MONDO:0005041 / 22 / glaucoma
  7. MONDO:0004568 / 20 / paralytic ileus
  8. MONDO:0005098 / 19 / stroke disorder
  9. MONDO:0005044 / 16 / hypertension
  10. MONDO:0001823 / 15 / sick sinus syndrome

## Implementation
- `app/modules/contraindications/domain/disease_mapping.py` --
  `DISEASE_TO_MONDO` (11 ключів: 10 хвороб + 2 форми запису
  hypertension -- "гіпертонія" і "артеріальна гіпертензія" на один
  MONDO ID, явне рішення користувача), `normalize_to_mondo()`
  (exact-token-match, той самий принцип, що `normalize_to_chebi()`).
- **Розміщення -- локальне, НЕ `app/shared/`.** На відміну від
  `BRAND_TO_SUBSTANCE` (виносився в shared після ДРУГОГО
  підтвердженого споживача, ADR-0012), тут Contraindications --
  ПЕРШИЙ споживач: Diseases-модуль не має жодної логіки мапінгу
  сьогодні. Виносити -- тільки після другого підтвердженого
  споживача, той самий коментар-попередження в коді.
- `tests/modules/contraindications/test_disease_mapping.py` -- 17
  тестів: усі 10 хвороб, обидві форми hypertension + перевірка, що
  вони резолвляться в один MONDO ID, case/whitespace insensitivity,
  unknown -> None, порожній рядок -> None, узгодженість словника
  (рівно 11 записів, усі значення -- валідні MONDO CURIE).

## Українські відповідники -- джерело рішення
Запропоновані мною як загальновживані медичні терміни без
діалектної/регіональної неоднозначності, ЯВНО підтверджені
користувачем (включно з рішенням про два ключі для hypertension) --
не прийняті скриптом мовчки. Задокументовано в docstring
`disease_mapping.py`.

## Чесно зафіксована межа (ADR-0014, оновлення S07E04)
Наявність словника НЕ означає перевірку на реальних даних. Жодного
реального запису Disease в БД немає -- ланцюжок `diagnosis_name ->
DISEASE_TO_MONDO -> MONDO` перевірений лише на 11 літеральних рядках,
які самі є ключами словника. Той самий факт стосується
Medications.drug_name -> BRAND_TO_SUBSTANCE -> CHEBI. Рішення писати
Application-шар зараз -- окреме, не прийняте цим епізодом.

## Verification
Sandbox: 17/17 pytest (pure Python, без DB/ORM -- як
substance_mapping.py). Реальний venv -- команда нижче, ще не
підтверджено користувачем.
