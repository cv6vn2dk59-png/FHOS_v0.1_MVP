from app.modules.clinical_reasoning.domain.entities import (
    ClinicalHypothesis,
    EvidenceLevel,
    HealthNode,
    HypothesisOrigin,
    HypothesisStatus,
    check_hypothesis_expansion,
)


def make_hypothesis(
    title="Test",
    mechanism="test mechanism",
    origin=HypothesisOrigin.SYSTEM_GENERATED,
    anatomical_source=None,
    body_system=None,
    etiology_category=None,
    status=HypothesisStatus.CANDIDATE,
    source_ids=None,
):
    return ClinicalHypothesis(
        symptom_node_id="HP:0003077",
        title=title,
        mechanism=mechanism,
        origin=origin,
        evidence_level=EvidenceLevel.LEVEL_3,
        anatomical_source=anatomical_source,
        body_system=body_system,
        etiology_category=etiology_category,
        status=status,
        source_ids=source_ids or [],
    )


class TestHealthNodeValidation:
    def test_raises_when_external_id_empty(self):
        import pytest
        with pytest.raises(ValueError):
            HealthNode(external_id="", external_source="HPO", label="test", node_kind="Symptom")

    def test_raises_when_external_source_empty(self):
        import pytest
        with pytest.raises(ValueError):
            HealthNode(external_id="HP:0003077", external_source="", label="test", node_kind="Symptom")

    def test_valid_node_created(self):
        node = HealthNode(external_id="HP:0003077", external_source="HPO",
                           label="Knee pain", node_kind="Symptom")
        assert node.external_id == "HP:0003077"


class TestClinicalHypothesisValidation:
    def test_raises_when_title_empty(self):
        import pytest
        with pytest.raises(ValueError):
            make_hypothesis(title="")

    def test_raises_when_mechanism_empty(self):
        import pytest
        with pytest.raises(ValueError):
            make_hypothesis(mechanism="")


class TestIndependenceKey:
    def test_different_mechanisms_have_different_keys(self):
        h1 = make_hypothesis(mechanism="cartilage degeneration", anatomical_source="joint")
        h2 = make_hypothesis(mechanism="nerve compression", anatomical_source="spine")
        assert h1.independence_key() != h2.independence_key()

    def test_same_mechanism_and_source_have_same_key(self):
        h1 = make_hypothesis(title="A", mechanism="cartilage degeneration", anatomical_source="joint")
        h2 = make_hypothesis(title="B (rephrased)", mechanism="cartilage degeneration", anatomical_source="joint")
        assert h1.independence_key() == h2.independence_key()

    def test_case_insensitive(self):
        h1 = make_hypothesis(mechanism="Cartilage Degeneration")
        h2 = make_hypothesis(mechanism="cartilage degeneration")
        assert h1.independence_key() == h2.independence_key()


class TestUserEchoProhibition:
    """Пряма перевірка моєї власної помилки з S07E09 (Додаток A, 4.3):
    система не має права видати ТІЛЬКИ повторення гіпотези користувача.
    """

    def test_only_user_supplied_violates_expansion(self):
        hypotheses = [make_hypothesis(origin=HypothesisOrigin.USER_SUPPLIED)]
        violations = check_hypothesis_expansion(hypotheses)
        assert any("User Echo Prohibition" in v for v in violations)

    def test_user_supplied_plus_system_generated_passes(self):
        hypotheses = [
            make_hypothesis(title="Hip-spine syndrome (user)", mechanism="nerve compression",
                             anatomical_source="spine", origin=HypothesisOrigin.USER_SUPPLIED),
            make_hypothesis(title="Joint inflammation", mechanism="inflammatory process",
                             anatomical_source="joint", origin=HypothesisOrigin.SYSTEM_GENERATED),
        ]
        violations = check_hypothesis_expansion(hypotheses)
        assert not any("User Echo Prohibition" in v for v in violations)

    def test_empty_list_is_violation(self):
        violations = check_hypothesis_expansion([])
        assert len(violations) == 1
        assert "порожній" in violations[0]


class TestIndependenceRuleDetection:
    def test_detects_duplicate_rephrased_hypothesis(self):
        hypotheses = [
            make_hypothesis(title="Joint wear (osteoarthritis)", mechanism="cartilage degeneration",
                             anatomical_source="joint", origin=HypothesisOrigin.SYSTEM_GENERATED),
            make_hypothesis(title="Degenerative joint disease (same thing, reworded)",
                             mechanism="cartilage degeneration", anatomical_source="joint",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
        ]
        violations = check_hypothesis_expansion(hypotheses)
        assert any("Independence Rule" in v for v in violations)

    def test_six_real_knee_pain_branches_pass_independence(self):
        """Реальний перевірений приклад з S07E09 -- 6 гілок для 'болить коліно'."""
        hypotheses = [
            make_hypothesis(title="Osteoarthritis", mechanism="cartilage degeneration",
                             anatomical_source="joint", body_system="musculoskeletal",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
            make_hypothesis(title="Inflammatory arthritis", mechanism="inflammatory process",
                             anatomical_source="joint", body_system="immune",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
            make_hypothesis(title="Meniscus injury", mechanism="mechanical tear",
                             anatomical_source="meniscus", body_system="musculoskeletal",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
            make_hypothesis(title="Referred pain from hip/spine", mechanism="nerve referral",
                             anatomical_source="spine", body_system="nervous",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
            make_hypothesis(title="Vascular cause", mechanism="circulation impairment",
                             anatomical_source="blood vessels", body_system="circulatory",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
            make_hypothesis(title="Septic arthritis", mechanism="bacterial infection",
                             anatomical_source="joint", body_system="immune",
                             etiology_category="infectious",
                             origin=HypothesisOrigin.SYSTEM_GENERATED),
        ]
        violations = check_hypothesis_expansion(hypotheses)
        independence_violations = [v for v in violations if "Independence Rule" in v]
        assert len(independence_violations) == 0


class TestDiagnosticBoundaryRule:
    def test_verified_system_generated_without_source_is_violation(self):
        hypotheses = [
            make_hypothesis(origin=HypothesisOrigin.USER_SUPPLIED),
            make_hypothesis(title="No source", mechanism="something",
                             origin=HypothesisOrigin.SYSTEM_GENERATED,
                             status=HypothesisStatus.VERIFIED, source_ids=[]),
        ]
        violations = check_hypothesis_expansion(hypotheses)
        assert any("Diagnostic Boundary Rule" in v for v in violations)

    def test_verified_with_source_is_not_violation(self):
        hypotheses = [
            make_hypothesis(origin=HypothesisOrigin.USER_SUPPLIED),
            make_hypothesis(title="Has source", mechanism="something else",
                             origin=HypothesisOrigin.SYSTEM_GENERATED,
                             status=HypothesisStatus.VERIFIED, source_ids=["PMID:12345"]),
        ]
        violations = check_hypothesis_expansion(hypotheses)
        assert not any("Diagnostic Boundary Rule" in v for v in violations)
