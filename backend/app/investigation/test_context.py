from app.investigation.context import InvestigationContext
from app.investigation.revision import RevisionFactory
from app.investigation.history import HistoryManager

ctx = InvestigationContext(

    case_id="case_1",

    revision=RevisionFactory.first()

)

HistoryManager.append(

    ctx,

    "context_created"

)

print()

print("CASE")

print(ctx.case_id)

print()

print("REVISION")

print(ctx.revision)

print()

print("HISTORY")

print(ctx.history)