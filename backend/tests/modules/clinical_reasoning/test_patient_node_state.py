from datetime import date, datetime

import pytest

from app.modules.clinical_reasoning.domain.entities import (
    PatientNodeState,
    find_shared_nodes,
)


def make_state(patient_id="patient_1", node_id="MONDO:staph",
                episode_id="episode_1", family_link_reason=None):
    return PatientNodeState(
        patient_id=patient_id, node_id=node_id, episode_id=episode_id,
        activated_at=datetime(2026, 1, 1), family_link_reason=family_link_reason,
    )


class TestValidation:
    def test_raises_when_patient_id_empty(self):
        with pytest.raises(ValueError):
            make_state(patient_id="")

    def test_raises_when_node_id_empty(self):
        with pytest.raises(ValueError):
            make_state(node_id="")

    def test_raises_when_episode_id_empty(self):
        with pytest.raises(ValueError):
            make_state(episode_id="")


class TestFindSharedNodes:
    def test_finds_the_family_cube_example(self):
        """Реальний приклад з S07E09: Staphylococcus aureus спільний
        для Чоловіка, Дружини, Дитини -- 'куб' на практиці."""
        states = [
            make_state(patient_id="husband", node_id="MONDO:staph",
                       family_link_reason="hereditary_relationship"),
            make_state(patient_id="wife", node_id="MONDO:staph",
                       family_link_reason="hereditary_relationship"),
            make_state(patient_id="child", node_id="MONDO:staph",
                       family_link_reason="hereditary_relationship"),
            make_state(patient_id="husband", node_id="MONDO:hip_spine_syndrome",
                       episode_id="episode_2"),
        ]
        shared = find_shared_nodes(states)
        assert "MONDO:staph" in shared
        assert set(shared["MONDO:staph"]) == {"husband", "wife", "child"}
        assert "MONDO:hip_spine_syndrome" not in shared

    def test_no_sharing_when_each_patient_has_own_unique_node(self):
        states = [
            make_state(patient_id="husband", node_id="A"),
            make_state(patient_id="wife", node_id="B"),
        ]
        shared = find_shared_nodes(states)
        assert shared == {}

    def test_same_patient_same_node_not_counted_as_shared(self):
        states = [
            make_state(patient_id="husband", node_id="A", episode_id="ep1"),
            make_state(patient_id="husband", node_id="A", episode_id="ep2"),
        ]
        shared = find_shared_nodes(states)
        assert shared == {}
