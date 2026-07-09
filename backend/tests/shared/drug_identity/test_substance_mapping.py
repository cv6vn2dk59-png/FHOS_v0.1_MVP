from app.shared.drug_identity.substance_mapping import (
    BRAND_TO_SUBSTANCE,
    SUBSTANCE_TO_CHEBI,
    normalize_to_chebi,
)


class TestNormalizeToChebiKnownSubstances:
    """Реальні значення, підтверджені на MeDIC Drug List.csv (S07E03)."""

    def test_warfarin(self):
        assert normalize_to_chebi("warfarin") == "CHEBI:10033"

    def test_amiodarone(self):
        assert normalize_to_chebi("amiodarone") == "CHEBI:2663"

    def test_sertraline(self):
        assert normalize_to_chebi("sertraline") == "CHEBI:9123"

    def test_tranylcypromine(self):
        """CHEBI:9653 -- сіль-форма (SULPHATE), прийнята як еквівалент
        явним Architect-рівня рішенням (S07E03), НЕ автоматично
        алгоритмом точного токен-збігу (той не знаходить CHEBI для
        базової форми -- див. docstring substance_mapping.py)."""
        assert normalize_to_chebi("tranylcypromine") == "CHEBI:9653"


class TestNormalizeToChebiViaBrandName:
    def test_resolves_ukrainian_brand_name_to_chebi(self):
        assert normalize_to_chebi("кордарон") == "CHEBI:2663"

    def test_resolves_ukrainian_generic_name_to_chebi(self):
        assert normalize_to_chebi("варфарин") == "CHEBI:10033"

    def test_case_and_whitespace_insensitive(self):
        assert normalize_to_chebi("  WARFARIN  ") == "CHEBI:10033"


class TestNormalizeToChebiUnknownSubstance:
    def test_returns_none_for_unmapped_substance(self):
        assert normalize_to_chebi("ібупрофен") is None

    def test_returns_none_for_unmapped_english_name(self):
        assert normalize_to_chebi("ibuprofen") is None


class TestDictionaryConsistency:
    """Кожна речовина з BRAND_TO_SUBSTANCE.values() має запис у
    SUBSTANCE_TO_CHEBI -- інакше normalize_to_chebi() мовчки поверне
    None для брендів, що мали б резолвитись."""

    def test_every_brand_target_substance_has_chebi_entry(self):
        for substance in BRAND_TO_SUBSTANCE.values():
            assert substance in SUBSTANCE_TO_CHEBI, (
                f"{substance!r} є ціллю BRAND_TO_SUBSTANCE, "
                f"але відсутня в SUBSTANCE_TO_CHEBI"
            )
