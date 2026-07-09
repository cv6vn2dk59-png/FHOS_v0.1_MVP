"""Речовина-ідентичність: "введена назва" -> substance -> CHEBI.

ADR-0012 передбачив цей момент явно: "як тільки з'явиться другий
реальний споживач (не Drug Interactions), виносити мапінг в окремий
компонент". Contraindications (CHEBI-based, ADR-0014) -- цей другий
споживач (S07E01/E03). BRAND_TO_SUBSTANCE перенесено сюди як є з
drug_interactions/domain/name_mapping.py -- Drug Interactions тепер
імпортує його звідси, не дублює.

SUBSTANCE_TO_CHEBI -- новий шар, побудований з MeDIC Drug List.csv
(scripts/build_substance_to_chebi.py, документує точний алгоритм
резолюції). Статичний словник, НЕ парситься з CSV у runtime -- той
самий підхід, що BRAND_TO_SUBSTANCE і PHANSALKAR_2013_INTERACTIONS:
маленький, підтверджений набір фактів компілюється один раз, а не
перечитується щоразу (Drug Interactions і Contraindications
викликають normalize_to_chebi()/normalize_drug_name() у hot path,
на кожен запит -- залежність від зовнішнього CSV-файлу там була б
неправильною).

Побудова тільки для 4 речовин з BRAND_TO_SUBSTANCE.values() -- НЕ
повна таблиця для всіх препаратів MeDIC (Confirmed Repetition, not
Confirmed Intention -- той самий принцип, що вже застосований до
active_substances/clinical_moieties в ADR-0014). Розширення -- коли
з'явиться конкретна нова речовина в реальному використанні.

tranylcypromine -- задокументований виняток. Точний токен-збіг
"tranylcypromine" у MeDIC Drug List.csv веде на
PUBCHEM.COMPOUND:73417116 (не CHEBI). Єдиний CHEBI-рядок --
CHEBI:9653, drug_name="TRANYLCYPROMINE SULPHATE" (сіль-форма, не
точний збіг за базовим алгоритмом). Явне рішення (Architect-рівня,
S07E03): прийняти CHEBI:9653 як еквівалент -- сіль тієї ж речовини,
жодних інших CHEBI-варіантів у файлі немає.
"""

BRAND_TO_SUBSTANCE: dict[str, str] = {
    "варфарин": "warfarin",
    "кордарон": "amiodarone",
    "аміодарон": "amiodarone",
    "сертралін": "sertraline",
    "транілципромін": "tranylcypromine",
}

# Побудовано scripts/build_substance_to_chebi.py з MeDIC Drug List.csv
# (реальний запуск, S07E03). tranylcypromine -- виняток, див. docstring.
SUBSTANCE_TO_CHEBI: dict[str, str] = {
    "warfarin": "CHEBI:10033",
    "amiodarone": "CHEBI:2663",
    "sertraline": "CHEBI:9123",
    "tranylcypromine": "CHEBI:9653",
}


def normalize_to_chebi(entered_name: str) -> str | None:
    """"Введена назва" (бренд чи речовина, укр./англ.) -> CHEBI ID.

    None, якщо речовина не входить у поточний підтверджений набір
    (SUBSTANCE_TO_CHEBI) -- явна відсутність відповіді, не здогадка.
    """
    key = entered_name.strip().lower()
    substance = BRAND_TO_SUBSTANCE.get(key, key)
    return SUBSTANCE_TO_CHEBI.get(substance)
