"""Локальна таблиця "введена назва -> назва речовини".

ADR-0012: живе тут навмисно, для v1. Єдиний підтверджений споживач --
Drug Interactions. Як тільки з'явиться другий реальний (не гіпотетичний)
споживач -- винести в окремий компонент, не копіювати цей словник.
"""

# v1 local mapping. Extract only after second confirmed consumer. See ADR-0012.
BRAND_TO_SUBSTANCE: dict[str, str] = {
    "варфарин": "warfarin",
    "кордарон": "amiodarone",
    "аміодарон": "amiodarone",
}


def normalize_drug_name(entered_name: str) -> str:
    key = entered_name.strip().lower()
    return BRAND_TO_SUBSTANCE.get(key, key)
