from app.modules.contraindications.domain.disease_mapping import (
    DISEASE_TO_MONDO,
    normalize_to_mondo,
)


class TestNormalizeToMondoKnownDiseases:
    """Реальні MONDO ID, перевірені на Contraindications List.csv (S07E04)."""

    def test_asthma(self):
        assert normalize_to_mondo("астма") == "MONDO:0004979"

    def test_heart_failure(self):
        assert normalize_to_mondo("серцева недостатність") == "MONDO:0005252"

    def test_myocardial_infarction(self):
        assert normalize_to_mondo("інфаркт міокарда") == "MONDO:0005068"

    def test_anuria(self):
        assert normalize_to_mondo("анурія") == "MONDO:0002476"

    def test_cardiogenic_shock(self):
        assert normalize_to_mondo("кардіогенний шок") == "MONDO:0800175"

    def test_glaucoma(self):
        assert normalize_to_mondo("глаукома") == "MONDO:0005041"

    def test_paralytic_ileus(self):
        assert normalize_to_mondo("паралітична кишкова непрохідність") == "MONDO:0004568"

    def test_stroke(self):
        assert normalize_to_mondo("інсульт") == "MONDO:0005098"

    def test_sick_sinus_syndrome(self):
        assert normalize_to_mondo("синдром слабкості синусового вузла") == "MONDO:0001823"


class TestNormalizeToMondoHypertensionDualForms:
    """Два ключі -> один MONDO ID, явне рішення користувача (S07E04)."""

    def test_short_form(self):
        assert normalize_to_mondo("гіпертонія") == "MONDO:0005044"

    def test_full_form(self):
        assert normalize_to_mondo("артеріальна гіпертензія") == "MONDO:0005044"

    def test_both_forms_resolve_to_same_mondo_id(self):
        assert normalize_to_mondo("гіпертонія") == normalize_to_mondo(
            "артеріальна гіпертензія"
        )


class TestNormalizeToMondoCaseAndWhitespace:
    def test_case_and_whitespace_insensitive(self):
        assert normalize_to_mondo("  АСТМА  ") == "MONDO:0004979"


class TestNormalizeToMondoUnknownDisease:
    def test_returns_none_for_unmapped_diagnosis(self):
        assert normalize_to_mondo("панкреатит") is None

    def test_returns_none_for_empty_string(self):
        assert normalize_to_mondo("") is None


class TestDictionaryContents:
    def test_exactly_eleven_entries(self):
        """10 хвороб + 2 форми запису hypertension = 11 ключів."""
        assert len(DISEASE_TO_MONDO) == 11

    def test_all_values_are_valid_mondo_curies(self):
        for value in DISEASE_TO_MONDO.values():
            assert value.startswith("MONDO:")
