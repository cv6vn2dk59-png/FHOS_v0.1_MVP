"""
FHOS Default Workflows

Workflows are data, not hardcoded engine logic.
"""


DEFAULT_CLINICAL_INVESTIGATION_WORKFLOW = {
    "id": "clinical_investigation_default",
    "title": "Default Clinical Investigation Workflow",
    "states": [
        "new",
        "triage",
        "investigation",
        "waiting_data",
        "medical_board",
        "decision",
        "follow_up",
        "closed",
    ],
    "transitions": {
        "new": "triage",
        "triage": "investigation",
        "investigation": "waiting_data",
        "waiting_data": "medical_board",
        "medical_board": "decision",
        "decision": "follow_up",
        "follow_up": "closed",
    },
}