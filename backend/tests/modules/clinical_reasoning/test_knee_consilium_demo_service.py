from app.modules.clinical_reasoning.api.routes import demo_knee_consilium
from app.modules.clinical_reasoning.application.knee_consilium_demo_service import (
    KneePainConsiliumDemoService,
)


def test_knee_consilium_demo_keeps_six_independent_branches_visible():
    payload = KneePainConsiliumDemoService().build()

    domains = {branch.causal_domain for branch in payload["branches"]}
    assert domains == {
        "degenerative",
        "inflammatory",
        "mechanical_internal",
        "referred_pain",
        "vascular",
        "infectious",
    }
    assert payload["result"].consensus.retained_branch_ids == sorted(
        branch.id for branch in payload["branches"]
    )


def test_knee_consilium_demo_preserves_safety_alternatives():
    payload = KneePainConsiliumDemoService().build()

    unsafe_ids = set(payload["result"].consensus.unsafe_to_close_branch_ids)
    assert f"{payload['case_id']}:branch:inflammatory" in unsafe_ids
    assert f"{payload['case_id']}:branch:vascular" in unsafe_ids
    assert f"{payload['case_id']}:branch:infectious" in unsafe_ids
    assert not any(
        violation.code in {"branch_without_review", "consilium_flattened_graph"}
        for violation in payload["result"].violations
    )


def test_knee_consilium_demo_route_returns_readable_example():
    payload = demo_knee_consilium()

    assert payload["symptom"] == "болить коліно"
    assert len(payload["branches"]) == 6
    assert payload["consilium"]["consensus"]["leading_branch_ids"] == [
        "KNEE-DEMO-001:branch:mechanical_internal"
    ]
