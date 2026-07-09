# ADR-0014: Contraindications v1 -- Domain Scope

## Статус
Прийнято (Architect Session завершено для domain-шару; application/persistence/API -- окремі кроки).

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
