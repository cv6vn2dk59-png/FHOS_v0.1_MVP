"""
FHOS AI Operating System
Clinical Working Memory

Dynamic, expandable clinical context for one medical task.
"""


class ClinicalWorkingMemory:

    def build(self, request: str, capability_name: str):

        return {
            "request": request,
            "capability": capability_name,
            "mode": "dynamic",
            "core_context": [],
            "expanded_context": [],
            "possible_links": [],
            "missing_data": [],
            "rules": {
                "use_only_relevant_data": True,
                "allow_context_expansion": True,
                "do_not_load_full_patient_history": True,
                "expand_if_medically_reasonable": True,
            },
            "safety": {
                "final_decision": "не приймати клінічних рішень без лікаря",
                "status": "context_prepared",
            },
        }