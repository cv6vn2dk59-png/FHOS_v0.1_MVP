from datetime import datetime, timedelta, timezone

import pytest

from app.modules.clinical_reasoning.domain.causality import ProvenanceReference
from app.modules.clinical_reasoning.domain.temporal_causality import (
    CausalTemporalLink,
    ClinicalEventKind,
    ClinicalTimelineEvent,
    TemporalCausalityEngine,
    TemporalInterval,
    TemporalPrecision,
    TemporalRelationKind,
)


PROV = [ProvenanceReference(source_id="TEST", source_version="1")]


def dt(day: int):
    return datetime(2026, 7, day, tzinfo=timezone.utc)


def event(event_id: str, start=None, end=None, branch_ids=None):
    return ClinicalTimelineEvent(
        id=event_id,
        case_id="CASE-1",
        kind=ClinicalEventKind.OTHER,
        label=event_id,
        interval=TemporalInterval(
            earliest_start=start,
            latest_start=start,
            earliest_end=end or start,
            latest_end=end or start,
            precision=TemporalPrecision.EXACT if start else TemporalPrecision.UNKNOWN,
        ),
        provenance=PROV,
        branch_ids=branch_ids or [],
    )


def test_interval_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        TemporalInterval(earliest_start=dt(3), latest_start=dt(2))


def test_event_requires_provenance():
    with pytest.raises(ValueError):
        ClinicalTimelineEvent(
            id="e1", case_id="CASE-1", kind=ClinicalEventKind.OTHER,
            label="x", interval=TemporalInterval(), provenance=[]
        )


def test_definite_before_relation():
    engine = TemporalCausalityEngine()
    relation = engine.compare(event("a", dt(1)), event("b", dt(3)))
    assert relation.relation_kind == TemporalRelationKind.BEFORE
    assert relation.certainty == 1.0


def test_unknown_date_remains_indeterminate():
    engine = TemporalCausalityEngine()
    relation = engine.compare(event("a"), event("b", dt(3)))
    assert relation.relation_kind == TemporalRelationKind.INDETERMINATE


def test_cause_after_effect_is_conflict():
    events = [event("cause", dt(5), branch_ids=["b1"]), event("effect", dt(1), branch_ids=["b1"])]
    link = CausalTemporalLink(
        id="l1", source_event_id="cause", target_event_id="effect",
        relation_type="may_cause", provenance=PROV, confidence=0.8,
    )
    result = TemporalCausalityEngine().evaluate("CASE-1", events, [link])
    assert [c.conflict_type for c in result.conflicts] == ["cause_after_effect"]
    assert result.branch_assessments[0].coherence_status == "conflicted"


def test_overlapping_intervals_create_missing_temporal_evidence_not_false_conflict():
    first = ClinicalTimelineEvent(
        id="a", case_id="CASE-1", kind=ClinicalEventKind.OTHER, label="a",
        interval=TemporalInterval(
            earliest_start=dt(1), latest_start=dt(4), earliest_end=dt(2), latest_end=dt(5),
            precision=TemporalPrecision.INTERVAL,
        ), provenance=PROV, branch_ids=["b1"]
    )
    second = ClinicalTimelineEvent(
        id="b", case_id="CASE-1", kind=ClinicalEventKind.OTHER, label="b",
        interval=TemporalInterval(
            earliest_start=dt(3), latest_start=dt(6), earliest_end=dt(4), latest_end=dt(7),
            precision=TemporalPrecision.INTERVAL,
        ), provenance=PROV, branch_ids=["b1"]
    )
    link = CausalTemporalLink(id="l", source_event_id="a", target_event_id="b", relation_type="may_cause", provenance=PROV)
    result = TemporalCausalityEngine().evaluate("CASE-1", [first, second], [link])
    assert result.conflicts == []
    assert result.missing_evidence
    assert result.branch_assessments[0].coherence_status == "indeterminate"


def test_minimum_lag_violation_detected():
    events = [event("a", dt(1)), event("b", dt(2))]
    link = CausalTemporalLink(
        id="l", source_event_id="a", target_event_id="b", relation_type="may_cause",
        provenance=PROV, minimum_lag=timedelta(days=3),
    )
    result = TemporalCausalityEngine().evaluate("CASE-1", events, [link])
    assert result.conflicts[0].conflict_type == "minimum_lag_violation"


def test_maximum_lag_violation_detected():
    events = [event("a", dt(1)), event("b", dt(10))]
    link = CausalTemporalLink(
        id="l", source_event_id="a", target_event_id="b", relation_type="may_cause",
        provenance=PROV, maximum_lag=timedelta(days=3),
    )
    result = TemporalCausalityEngine().evaluate("CASE-1", events, [link])
    assert result.conflicts[0].conflict_type == "maximum_lag_violation"


def test_temporal_precedence_not_reported_as_causality():
    events = [event("a", dt(1)), event("b", dt(2))]
    result = TemporalCausalityEngine().evaluate("CASE-1", events, [])
    assert any("does not establish causality" in item for item in result.limitations)


def test_unknown_event_generates_question_without_invented_date():
    result = TemporalCausalityEngine().evaluate("CASE-1", [event("unknown")], [])
    assert result.ordered_event_ids == ["unknown"]
    assert result.missing_evidence[0].event_ids == ["unknown"]
    assert "When did" in result.missing_evidence[0].question


def test_events_from_other_case_are_rejected():
    wrong = event("x", dt(1))
    wrong.case_id = "OTHER"
    with pytest.raises(ValueError):
        TemporalCausalityEngine().evaluate("CASE-1", [wrong], [])


def test_unknown_link_event_is_warning_not_crash():
    result = TemporalCausalityEngine().evaluate(
        "CASE-1", [event("a", dt(1))],
        [CausalTemporalLink(id="l", source_event_id="a", target_event_id="missing", relation_type="may_cause", provenance=PROV)],
    )
    assert "causal_link_references_unknown_event" in result.warnings
