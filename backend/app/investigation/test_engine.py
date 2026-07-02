"""
Manual Investigation Engine Test
"""

from app.investigation.engine import InvestigationEngine


engine = InvestigationEngine()

context = engine.create_context("case_1")

event = {
    "id": "event_1",
    "type": "user_request",
    "payload": {
        "text": "У мене болить голова третій день"
    },
}

context = engine.step(context, event)

print()
print("CASE:", context.case_id)
print("REVISION:", context.revision.revision)
print("OBSERVATIONS:", context.observations)
print("VALIDATED:", context.validated_evidence)
print("GAPS:", context.gaps)
print("NEXT QUESTION:", context.next_question)
print("HISTORY:", context.history)
print()

print("OBJECTIVES")

print(context.objectives)

print()

print("GAPS")

print(context.gaps)

print()

print("QUESTION CANDIDATES")

print(context.question_candidates)

print()

print("NEXT QUESTION")

print(context.next_question)