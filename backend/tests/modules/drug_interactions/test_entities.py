import pytest

from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    InteractionSeverity,
    find_interactions,
)
from app.modules.drug_interactions.domain.phansalkar_2013 import (
    PHANSALKAR_2013_INTERACTIONS,
)


def make_interaction(side_a=None, side_b=None) -> DrugInteraction:
    if side_a is None:
        side_a = ["warfarin"]
    if side_b is None:
        side_b = ["amiodarone"]
    return DrugInteraction(
        side_a=side_a,
        side_b=side_b,
        severity=InteractionSeverity.CONTRAINDICATED,
        description="test interaction",
        knowledge_source_id="test_source",
    )


class TestValidation:
    def test_raises_when_side_a_empty(self):
        with pytest.raises(ValueError):
            make_interaction(side_a=[])

    def test_raises_when_side_b_empty(self):
        with pytest.raises(ValueError):
            make_interaction(side_b=[])

    def test_raises_when_substance_appears_on_both_sides(self):
        with pytest.raises(ValueError):
            make_interaction(side_a=["warfarin"], side_b=["Warfarin"])


class TestPairKeySymmetry:
    def test_pair_key_same_regardless_of_side_order(self):
        i1 = make_interaction(side_a=["warfarin"], side_b=["amiodarone"])
        i2 = make_interaction(side_a=["amiodarone"], side_b=["warfarin"])
        assert i1.pair_key() == i2.pair_key()

    def test_pair_key_case_insensitive(self):
        i1 = make_interaction(side_a=["Warfarin"], side_b=["Amiodarone"])
        i2 = make_interaction(side_a=["warfarin"], side_b=["amiodarone"])
        assert i1.pair_key() == i2.pair_key()


class TestMatches:
    def test_matches_when_both_sides_present(self):
        interaction = make_interaction(side_a=["warfarin"], side_b=["amiodarone"])
        assert interaction.matches({"warfarin", "amiodarone"})

    def test_does_not_match_when_only_one_side_present(self):
        interaction = make_interaction(side_a=["warfarin"], side_b=["amiodarone"])
        assert not interaction.matches({"warfarin"})

    def test_matches_case_insensitive(self):
        interaction = make_interaction(side_a=["warfarin"], side_b=["amiodarone"])
        assert interaction.matches({"Warfarin", "AMIODARONE"})

    def test_matches_class_side_with_any_member(self):
        interaction = make_interaction(
            side_a=["fluoxetine", "sertraline"], side_b=["tranylcypromine"]
        )
        assert interaction.matches({"sertraline", "tranylcypromine"})


class TestFindInteractions:
    def test_finds_known_interaction(self):
        known = [make_interaction(side_a=["warfarin"], side_b=["amiodarone"])]
        result = find_interactions(["warfarin", "amiodarone"], known)
        assert len(result) == 1

    def test_finds_nothing_when_no_match(self):
        known = [make_interaction(side_a=["warfarin"], side_b=["amiodarone"])]
        result = find_interactions(["paracetamol"], known)
        assert len(result) == 0

    def test_finds_multiple_when_several_match(self):
        known = [
            make_interaction(side_a=["warfarin"], side_b=["amiodarone"]),
            make_interaction(side_a=["warfarin"], side_b=["fluconazole"]),
        ]
        result = find_interactions(["warfarin", "amiodarone", "fluconazole"], known)
        assert len(result) == 2


class TestPhansalkarDataset:
    def test_exactly_15_interactions(self):
        assert len(PHANSALKAR_2013_INTERACTIONS) == 15

    def test_all_have_knowledge_source(self):
        assert all(
            i.knowledge_source_id == "phansalkar_2013"
            for i in PHANSALKAR_2013_INTERACTIONS
        )

    def test_maoi_ssri_interaction_detected(self):
        result = find_interactions(
            ["sertraline", "tranylcypromine"], PHANSALKAR_2013_INTERACTIONS
        )
        assert len(result) == 1

    def test_warfarin_amiodarone_not_in_this_dataset(self):
        result = find_interactions(["warfarin", "amiodarone"], PHANSALKAR_2013_INTERACTIONS)
        assert len(result) == 0
