"""
FHOS Workflow Core

Generic workflow engine.
No medical logic here.
"""


class WorkflowEngine:

    def next_state(self, workflow: dict, current_state: str):

        transitions = workflow.get("transitions", {})

        return transitions.get(current_state)