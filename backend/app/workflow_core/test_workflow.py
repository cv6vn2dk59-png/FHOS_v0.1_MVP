"""
Manual workflow test
"""

from app.workflow_core.engine import WorkflowEngine
from app.workflow_core.default_workflows import DEFAULT_CLINICAL_INVESTIGATION_WORKFLOW


engine = WorkflowEngine()

current_state = "new"

next_state = engine.next_state(
    DEFAULT_CLINICAL_INVESTIGATION_WORKFLOW,
    current_state,
)

print("current_state:", current_state)
print("next_state:", next_state)