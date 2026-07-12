import pytest

from app.modules.clinical_reasoning.domain.entities import (
    EvidenceLevel,
    HealthRelation,
    RelationKind,
    find_neighbors,
)


def make_relation(from_id="HP:0003077", to_id="MONDO:0005044",
                   kind=RelationKind.CAN_EXPLAIN, citation="PMID:12345678"):
    return HealthRelation(
        from_node_id=from_id, to_node_id=to_id,
        relation_kind=kind, evidence_level=EvidenceLevel.LEVEL_3,
        source_citation=citation,
    )


class TestValidation:
    def test_raises_when_from_node_empty(self):
        with pytest.raises(ValueError):
            make_relation(from_id="")

    def test_raises_when_to_node_empty(self):
        with pytest.raises(ValueError):
            make_relation(to_id="")

    def test_raises_when_self_referencing(self):
        with pytest.raises(ValueError):
            make_relation(from_id="HP:0003077", to_id="HP:0003077")

    def test_raises_when_source_citation_empty(self):
        with pytest.raises(ValueError):
            make_relation(citation="")


class TestInvolves:
    def test_involves_from_node(self):
        r = make_relation(from_id="HP:0003077", to_id="MONDO:0005044")
        assert r.involves("HP:0003077")

    def test_involves_to_node(self):
        r = make_relation(from_id="HP:0003077", to_id="MONDO:0005044")
        assert r.involves("MONDO:0005044")

    def test_does_not_involve_unrelated_node(self):
        r = make_relation(from_id="HP:0003077", to_id="MONDO:0005044")
        assert not r.involves("HP:9999999")


class TestFindNeighbors:
    def test_finds_direct_neighbors_real_knee_example(self):
        """Реальний приклад з S07E09: 'болить коліно' -> кілька гілок."""
        relations = [
            make_relation("HP:knee_pain", "joint_osteoarthritis", RelationKind.CAN_EXPLAIN),
            make_relation("HP:knee_pain", "meniscus_injury", RelationKind.CAN_EXPLAIN),
            make_relation("HP:knee_pain", "hip_spine_referred", RelationKind.CAN_EXPLAIN),
            make_relation("unrelated_node", "something_else", RelationKind.ASSOCIATED_WITH),
        ]
        neighbors = find_neighbors("HP:knee_pain", relations)
        assert len(neighbors) == 3

    def test_finds_nothing_for_isolated_node(self):
        relations = [make_relation("HP:knee_pain", "joint_osteoarthritis")]
        neighbors = find_neighbors("HP:isolated", relations)
        assert len(neighbors) == 0
