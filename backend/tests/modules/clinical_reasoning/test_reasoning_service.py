from app.modules.clinical_reasoning.application.reasoning_service import ClinicalReasoningService
from app.modules.clinical_reasoning.domain.entities import ClinicalHypothesis, EvidenceLevel, HypothesisOrigin


def test_devil_review_rejects_user_echo_only():
    hypotheses = [
        ClinicalHypothesis(
            symptom_node_id="HP:1",
            title="User idea",
            mechanism="same idea",
            origin=HypothesisOrigin.USER_SUPPLIED,
            evidence_level=EvidenceLevel.LEVEL_4,
        )
    ]
    result = ClinicalReasoningService.devil_review(hypotheses)
    assert result["passed"] is False
    assert any("User Echo Prohibition" in item for item in result["violations"])


def test_devil_review_returns_three_required_questions():
    result = ClinicalReasoningService.devil_review([])
    assert len(result["questions"]) == 3
    assert result["passed"] is False
