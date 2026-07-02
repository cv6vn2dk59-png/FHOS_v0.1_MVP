"""
FHOS Event Engine

Entry point for all system events.
"""

from dataclasses import asdict

from app.event_core.router import ClinicalEventRouter
from app.event_core.case_matcher import CaseMatcher
from app.event_core.case_creator import CaseCreator
from app.intent.engine import IntentEngine
from app.evidence.engine import EvidenceEngine
from app.clinical_normalization.engine import ClinicalNormalizationEngine
from app.problem_list.engine import ProblemListEngine
from app.hypothesis.engine import HypothesisEngine
from app.evidence_analysis.engine import EvidenceAnalysisEngine
from app.triage.engine import TriageEngine
from app.workflow_core.engine import WorkflowEngine
from app.workflow_core.default_workflows import DEFAULT_CLINICAL_INVESTIGATION_WORKFLOW


class EventEngine:

    def __init__(self):
        self.router = ClinicalEventRouter()
        self.matcher = CaseMatcher()
        self.creator = CaseCreator()
        self.intent_engine = IntentEngine()
        self.evidence_engine = EvidenceEngine()
        self.normalization_engine = ClinicalNormalizationEngine()
        self.problem_engine = ProblemListEngine()
        self.hypothesis_engine = HypothesisEngine()
        self.analysis_engine = EvidenceAnalysisEngine()
        self.triage_engine = TriageEngine()
        self.workflow_engine = WorkflowEngine()

    def process(self, event: dict, open_cases: list[dict] | None = None):
        if open_cases is None:
            open_cases = []

        route = self.router.route(event)

        payload = event.get("payload", {})
        text = payload.get("text", "")

        intent_result = self.intent_engine.analyze(text)
        intent = asdict(intent_result)

        evidence = [
            asdict(item)
            for item in self.evidence_engine.build_from_event(event)
        ]

        normalized_statements = [
            asdict(item)
            for item in self.normalization_engine.normalize(evidence)
        ]

        problems = [
            asdict(problem)
            for problem in self.problem_engine.build_from_statements(
                statements=normalized_statements,
            )
        ]

        hypotheses = [
            asdict(item)
            for item in self.hypothesis_engine.build(
                problems=problems,
                evidence=evidence,
            )
        ]

        evidence_analysis = [
            asdict(item)
            for item in self.analysis_engine.analyze(
                hypotheses=hypotheses,
                evidence=evidence,
            )
        ]

        triage = asdict(
            self.triage_engine.assess(
                intent=intent,
                problems=problems,
                evidence=evidence,
            )
        )

        match = self.matcher.match(event, open_cases)

        created_case = None
        workflow_next_state = None

        if match.get("action") == "create_new_case":
            created_case = self.creator.create_from_event(event, intent)

            workflow_next_state = self.workflow_engine.next_state(
                DEFAULT_CLINICAL_INVESTIGATION_WORKFLOW,
                created_case["state"],
            )

        return {
            "event": event,
            "intent": intent,
            "evidence": evidence,
            "normalized_statements": normalized_statements,
            "problems": problems,
            "hypotheses": hypotheses,
            "evidence_analysis": evidence_analysis,
            "triage": triage,
            "patient_response_needed": triage.get("next_step") == "ask_critical_questions",
            "route": route,
            "case_match": match,
            "created_case": created_case,
            "workflow_next_state": workflow_next_state,
        }