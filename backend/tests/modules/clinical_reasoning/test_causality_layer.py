import pytest

from app.modules.clinical_reasoning.domain.causality import (
    CausalEdge, CausalPath, ContextConstraint, ProvenanceReference,
)


def prov():
    return [ProvenanceReference("source:test", "1")]


def test_causal_edge_requires_provenance():
    with pytest.raises(ValueError):
        CausalEdge("e", "a", "b", "may_contribute_to", "plausible", 0.5, [])


def test_causal_path_shape_is_validated():
    with pytest.raises(ValueError):
        CausalPath("p", ["a", "b", "c"], ["e1"], "glycemic_regulation", prov())


def test_context_constraint_is_preserved():
    constraint = ContextConstraint("fasting", "eq", True)
    path = CausalPath("p", ["fact", "mechanism"], ["e"], "glycemic_regulation", prov(), [constraint])
    assert path.context_constraints == [constraint]
