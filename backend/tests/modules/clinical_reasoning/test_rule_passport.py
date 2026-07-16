import pytest

from app.modules.clinical_reasoning.domain.evidence import EvidenceSourceType, EvidenceStrength
from app.modules.clinical_reasoning.domain.rule_passport import (
    RulePassport,
    RulePassportStatus,
    branch_evidence_rank,
    meets_closure_threshold,
)


def make_passport(**overrides):
    defaults = dict(
        rule_id="danger-branch-closure-v1",
        version="1.0",
        title="Закриття небезпечної гілки за порогом доказовості",
        status=RulePassportStatus.ACTIVE,
        source_type=EvidenceSourceType.CLINICAL_GUIDELINE,
        evidence_strength=EvidenceStrength.HIGH,
    )
    defaults.update(overrides)
    return RulePassport(**defaults)


def test_rule_passport_requires_non_empty_identity_fields():
    with pytest.raises(ValueError):
        make_passport(rule_id="  ")
    with pytest.raises(ValueError):
        make_passport(version="")
    with pytest.raises(ValueError):
        make_passport(title="")


def test_active_rule_passport_cannot_have_unrated_evidence():
    with pytest.raises(ValueError):
        make_passport(status=RulePassportStatus.ACTIVE, evidence_strength=EvidenceStrength.UNRATED)


def test_draft_rule_passport_may_have_unrated_evidence():
    passport = make_passport(status=RulePassportStatus.DRAFT, evidence_strength=EvidenceStrength.UNRATED)
    assert passport.status == RulePassportStatus.DRAFT


def test_rule_passport_carries_limitations_visibly():
    passport = make_passport(limitations=["Не валідовано на педіатричній популяції"])
    assert passport.limitations == ["Не валідовано на педіатричній популяції"]


# --- FHOS-RULE-R-14 -------------------------------------------------------

def test_branch_evidence_rank_orders_known_scale():
    assert branch_evidence_rank("speculative") < branch_evidence_rank("plausible")
    assert branch_evidence_rank("plausible") < branch_evidence_rank("supported")


def test_unknown_evidence_strength_ranks_below_known_scale():
    assert branch_evidence_rank("unknown_value") < branch_evidence_rank("speculative")


def test_meets_closure_threshold_true_when_strength_reaches_default_threshold():
    assert meets_closure_threshold("supported", clinician_confirmed=False) is True


def test_meets_closure_threshold_false_when_strength_below_default_threshold():
    assert meets_closure_threshold("plausible", clinician_confirmed=False) is False
    assert meets_closure_threshold("speculative", clinician_confirmed=False) is False


def test_clinician_confirmation_overrides_insufficient_evidence():
    assert meets_closure_threshold("speculative", clinician_confirmed=True) is True


def test_unknown_evidence_strength_never_passes_silently():
    assert meets_closure_threshold("mystery", clinician_confirmed=False) is False


def test_custom_threshold_is_respected():
    assert meets_closure_threshold("plausible", clinician_confirmed=False, threshold="plausible") is True
    assert meets_closure_threshold("speculative", clinician_confirmed=False, threshold="plausible") is False
