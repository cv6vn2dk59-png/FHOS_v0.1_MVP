# ADR-0014: Contraindications v1 -- Domain Scope

## Статус
Прийнято. Domain, persistence, application, API -- усі шари написані
(S07E05). Див. "Оновлення (S07E05)" нижче -- порожній результат API
НЕ означає "протипоказань немає", а лише "жодного збігу в маленьких
словниках".

## Контекст
Наступний Knowledge-модуль після Drug Interactions (речовина-речовина) і
Diseases (факт діагнозу): Contraindications -- речовина-хвороба, з
джерела MeDIC v1.

## Рішення

1. **Асиметрична модель.** На відміну від Drug Interactions
   (side_a/side_b, symmetric, pair_key()), тут substance і disease --
   різні типи сутностей, ніколи не можуть помінятись місцями. Тому
   pair_key() не існує в цьому модулі.

2. **severity відсутня.** MeDIC v1 не надає цих даних. Confirmed
   Repetition, not Confirmed Intention: немає підстави вигадувати
   шкалу без джерела, яке б її підтверджувало.

3. **Ідентифікатори -- CHEBI (речовина), MONDO (хвороба).** Усталені
   біомедичні онтології, CURIE-формат. Це свідомо інший вибір, ніж
   Medications (drug_name) і Diseases (diagnosis_name) -- вільний
   текст. Contraindication зберігає CHEBI/MONDO ID як рядок, без FK
   на ще не існуючу таблицю active_substances/clinical_moieties.
   Той самий тимчасовий підхід, що Drug Interactions v1 мав із
   name_mapping.py до появи реальної інфраструктури.

4. **Явно поза межами v1:**
   - Повна таблиця active_substances/clinical_moieties для всіх
     3857 препаратів MeDIC (окреме, велике рішення: чи вантажити
     весь Drug List, як валідувати заявлений 71%/29% розкол).
   - Мапінг Medications.drug_name -> CHEBI.
   - Мапінг Diseases.diagnosis_name -> MONDO.
   Обидва мапінги не розв'язані симетрично -- жоден модуль сьогодні
   не зберігає CHEBI/MONDO. Domain-шар Contraindications не потребує
   цих мапінгів (приймає готові ID), але Application-шар не зможе
   працювати з реальними записами пацієнта, поки хоч один бік не
   буде розв'язаний. Це усвідомлений розрив, не помилка.

## Наслідки
- Domain-шар (`Contraindication`, `find_contraindications()`) тестується
  ізольовано, з літеральними CHEBI/MONDO фікстурами -- так само, як
  Drug Interactions v1 на своєму першому кроці.
- Application/API-шари для Contraindications заблоковані до окремого
  рішення про хоча б один бік мапінгу (substance або disease).
- Якщо MeDIC v1 колись надасть severity, це стане окремою міграцією
  моделі, не розширенням поточної.

## Оновлення (S07E04, 2026-07-09) -- обидва мапінги технічно існують,
## жоден не підтверджений на реальних пацієнтських даних
Substance->CHEBI (S07E03, `app/shared/drug_identity/substance_mapping.py`)
і Diseases->MONDO (S07E04, `app/modules/contraindications/domain/
disease_mapping.py`, 11 ключів / 10 MONDO ID, топ-10 за частотою серед
374 унікальних MONDO у 1197 завантажених записах Contraindications)
тепер обидва існують. Це НЕ означає, що п.4 повністю закритий у тому
сенсі, що Medications-сторона мала регресію проти реальних тестів
Drug Interactions.

Жодного реального запису Disease в БД не існує -- лише тестові
фікстури. Ланцюжок `diagnosis_name (вільний текст пацієнта) ->
DISEASE_TO_MONDO -> MONDO` перевірений лише на 11 літеральних рядках,
які самі ж і є ключами словника (tautological coverage), не на
незалежному реальному вводі пацієнта. Той самий факт стосується і
Medications.drug_name -> BRAND_TO_SUBSTANCE -> CHEBI (S07E03: "не
перевірено на реальному Medications-записі").

Обидва словники -- локальні, exact-match, мінімального обсягу
(Confirmed Repetition): `SUBSTANCE_TO_CHEBI` покриває 4 речовини з
`BRAND_TO_SUBSTANCE.values()`, `DISEASE_TO_MONDO` -- 10 хвороб з
374 наявних MONDO ID. Розширення обох -- точкове, за появою реальної
потреби, не масове завчасне покриття.

Application-шар технічно можна писати (обидва боки формально мають
мапінг), але рішення писати його зараз -- ОКРЕМЕ архітектурне
рішення, не автоматичний наслідок наявності словників. Не приймається
цим оновленням.

## Оновлення (S07E05, 2026-07-09) -- application-шар написано
`ContraindicationService.check_patient(patient_profile_id)`
(app/modules/contraindications/application/service.py): читає АКТИВНІ
(is_active()==True) Medications і Diseases пацієнта, нормалізує через
normalize_to_chebi() / normalize_to_mondo(), шукає збіги через
find_contraindications(). Той самий патерн, що
DrugInteractionService.check_active_medications() -- читає facts з
інших модулів, нічого не змінює.

API: `GET /contraindications/patient/{patient_profile_id}` -- без
POST, read-only knowledge asset (той самий підхід, що ICD11NodeRead).

Свідомо задокументована в трьох місцях (docstring сервісу, docstring
route, тут) поведінкова межа: normalize_to_chebi()/normalize_to_mondo()
-- exact-match проти НАМІРЕНО малих словників (4 речовини, 10 хвороб).
Порожній результат від check_patient() НЕ означає "у пацієнта немає
протипоказань" -- здебільшого означає "жоден препарат/діагноз пацієнта
не потрапив у ці малі словники". Це прямий, очікуваний наслідок
Confirmed-Repetition обсягу обох словників, не помилка сервісу.
Клінічно покладатись на порожній результат як на "все гаразд" -- НЕ
можна, доки словники не розширяться на реальну потребу.

Тестів: 8 (application-шар, in-memory SQLite, включно з нормалізацією
брендової назви й альтернативної форми запису хвороби). API-шар
перевірено smoke-тестом через TestClient у пісочниці (200,
порожній список), формального TestClient-тесту в постійному наборі
не додано -- той самий відкритий backlog-пункт "API-рівня тести
відсутні як постійний шар" (PROJECT_STATE.md), не локальне рішення
цього модуля.
