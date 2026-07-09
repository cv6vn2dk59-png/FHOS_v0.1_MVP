"""Локальна таблиця "введена назва -> назва речовини".

ADR-0012 передбачив цей момент: "як тільки з'явиться другий реальний
споживач -- виносити мапінг в окремий компонент, не копіювати".
Contraindications (CHEBI-based, ADR-0014) -- цей другий споживач
(S07E03). BRAND_TO_SUBSTANCE тепер живе в
app/shared/drug_identity/substance_mapping.py -- імпортується звідси,
не дублюється. normalize_drug_name() лишається тут навмисно: це
domain-специфічна операція саме Drug Interactions (нормалізація для
side_a/side_b matching), не загальна утиліта -- на відміну від
normalize_to_chebi() у shared-модулі.
"""
from app.shared.drug_identity.substance_mapping import BRAND_TO_SUBSTANCE

__all__ = ["BRAND_TO_SUBSTANCE", "normalize_drug_name"]


def normalize_drug_name(entered_name: str) -> str:
    key = entered_name.strip().lower()
    return BRAND_TO_SUBSTANCE.get(key, key)
