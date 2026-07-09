# ADR-0012 — Medication Name Mapping lives inside Drug Interactions

## Статус
Прийнято.

## Рішення
Таблиця відповідності "назва препарату → діюча речовина" (наприклад,
"Варфарин Оріон" → "варфарин") для v1 живе локально всередині модуля
Drug Interactions, не як окремий сервіс і не як розширення Medications.
Причина: єдиний підтверджений споживач цієї таблиці — Drug Interactions.
Гіпотетичні майбутні споживачі (Medication Allergy, Medication Dosing,
Medication Search) поки не існують навіть як заплановані модулі — це
Confirmed Intention, не Confirmed Repetition, тому виносити mapping
в окремий компонент зараз передчасно.

Medications v1 навмисно не змінюється (жодного нового поля, жодної
міграції) — зберігає drug_name як вільний текст, введений користувачем,
без прив'язки до канонічної речовини. Це окреме, свідомо відкладене
питання нормалізації вводу, не предмет цього ADR.

## Наслідки
- Як тільки з'явиться другий реальний (не гіпотетичний) споживач цієї
  таблиці — вона виноситься з Drug Interactions в окремий компонент.
  Це не відкладена абстракція "про всяк випадок", а чітка умова: другий
  підтверджений consumer = сигнал переносити.
- У коді, там де визначена таблиця, залишається короткий коментар:
  "v1 local mapping. Extract only after second confirmed consumer."
  Повне обґрунтування — в цьому ADR, не в коментарі.
- Питання "чи Medications повинен зберігати канонічну діючу речовину
  окремо від введеної пацієнтом назви" залишається відкритим на майбутнє
  і не вирішується цим ADR.

## Оновлення (S07E03, 2026-07-09) — умова п.23 виконана
Другий реальний споживач з'явився: Contraindications (ADR-0014,
CHEBI-based). BRAND_TO_SUBSTANCE винесено з
`drug_interactions/domain/name_mapping.py` в
`app/shared/drug_identity/substance_mapping.py` -- Drug Interactions
імпортує його звідти (не дублює), `normalize_drug_name()` лишився в
Drug Interactions (domain-специфічна операція). Новий шар у тому ж
модулі -- `SUBSTANCE_TO_CHEBI` і `normalize_to_chebi()`, побудований
з `MeDIC Drug List.csv` (`scripts/build_substance_to_chebi.py`,
документує точний алгоритм: exact-token-match на полі `drug_name`,
перший рядок із `curie`, що має префікс `CHEBI:`).

Один задокументований виняток: `tranylcypromine` -- точний
токен-збіг веде на PUBCHEM (не CHEBI), єдиний CHEBI-рядок
(`CHEBI:9653`) -- сіль-форма ("TRANYLCYPROMINE SULPHATE"), що не
проходить точний збіг за базовим алгоритмом. Прийнято явним
Architect-рівня рішенням (не автоматично скриптом): CHEBI:9653 --
та сама речовина, інших CHEBI-варіантів у файлі немає.

Обсяг -- лише 4 речовини з поточного `BRAND_TO_SUBSTANCE.values()`,
НЕ повна таблиця для всіх препаратів MeDIC (Confirmed Repetition,
той самий принцип, що вже застосований до active_substances/
clinical_moieties, ADR-0014).