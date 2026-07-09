"""Diseases.diagnosis_name -> MONDO -- v1 стартовий словник.

Контекст: ADR-0014 п.4 -- Application-шар Contraindications заблокований,
поки хоч один бік (Medications.drug_name->CHEBI або
Diseases.diagnosis_name->MONDO) не матиме мапінгу. Substance->CHEBI
(S07E03) закрив першу половину. Цей файл -- друга половина, з тим самим
обмеженим обсягом.

Джерело даних -- НЕ вигадане. Кожен MONDO ID і англійська назва взяті
напряму з реального `Contraindications List.csv` (MeDIC), колонки
`final normalized disease id` / `final normalized disease label`,
відфільтровані за тим самим критерієм, що дає 1197 записів v1
(CHEBI+MONDO+high LLM confidence). Обрано топ-10 за частотою серед 374
унікальних MONDO ID у цьому наборі (перевірено напряму, S07E04).

Українські відповідники -- НЕ мовна експертиза автора коду. Це
загальновживані медичні терміни (астма, інсульт, гіпертонія тощо),
без діалектної/регіональної неоднозначності, запропоновані та явно
підтверджені користувачем (Architect-рівня рішення, S07E04), а не
мовчки вигадані скриптом -- та сама дисципліна, що вже застосована до
tranylcypromine (ADR-0012 "Оновлення") і до відмови від фабрикації
українського перекладу ICD-11.

Розміщення -- НЕ app/shared/. BRAND_TO_SUBSTANCE виносився в shared
тільки після другого підтвердженого споживача (ADR-0012). Для
Diseases->MONDO Contraindications -- ПЕРШИЙ споживач (Diseases-модуль
не має жодної логіки мапінгу сьогодні), тому словник лишається
локальним. Той самий коментар-попередження, що і в
substance_mapping.py: "v1 local mapping. Extract only after second
confirmed consumer."

Точний збіг (exact-token-match), без fuzzy-логіки -- той самий принцип,
що SUBSTANCE_TO_CHEBI. "гіпертонія" і "артеріальна гіпертензія" --
свідомо ДВА окремих ключі на один MONDO ID (природна варіативність
запису одного діагнозу, дешево покрити зараз, явне рішення
користувача, не автоматична нормалізація).

ВАЖЛИВО (чесно зафіксовано, не приховано): навіть із цим словником
ADR-0014 не розблокований у тому ж сенсі, що Medications-сторона.
Жодного реального записи Disease в БД не існує для перевірки
ланцюжка diagnosis_name (вільний текст пацієнта) -> DISEASE_TO_MONDO
-> MONDO. Регресія можлива лише проти тестових фікстур Diseases-модуля,
не проти реальних пацієнтських даних -- та сама якісна межа, що вже
явно названа для Medications.drug_name -> BRAND_TO_SUBSTANCE ->
SUBSTANCE_TO_CHEBI.
"""
from __future__ import annotations

DISEASE_TO_MONDO: dict[str, str] = {
    "астма": "MONDO:0004979",
    "серцева недостатність": "MONDO:0005252",
    "інфаркт міокарда": "MONDO:0005068",
    "анурія": "MONDO:0002476",
    "кардіогенний шок": "MONDO:0800175",
    "глаукома": "MONDO:0005041",
    "паралітична кишкова непрохідність": "MONDO:0004568",
    "інсульт": "MONDO:0005098",
    "гіпертонія": "MONDO:0005044",
    "артеріальна гіпертензія": "MONDO:0005044",
    "синдром слабкості синусового вузла": "MONDO:0001823",
}


def normalize_to_mondo(entered_name: str) -> str | None:
    """Diseases.diagnosis_name (вільний текст) -> MONDO ID, або None.

    v1 local mapping. Extract only after second confirmed consumer.
    """
    key = entered_name.strip().lower()
    return DISEASE_TO_MONDO.get(key)
