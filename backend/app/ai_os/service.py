"""
FHOS AI Operating System
Service
"""

from app.ai_os.board import MedicalBoard
from app.ai_os.clinical_working_memory import ClinicalWorkingMemory
from app.ai_os.consensus import ConsensusEngine
from app.ai_os.dispatcher import Dispatcher
from app.ai_os.planner import Planner
from app.ai_os.report import ReportBuilder
from app.ai_os.runtime import AIRuntime


planner = Planner()
dispatcher = Dispatcher()
board = MedicalBoard()
consensus = ConsensusEngine()
working_memory = ClinicalWorkingMemory()
report_builder = ReportBuilder()
ai_runtime = AIRuntime()


def ai_os_status():
    return {
        "module": "AI Operating System",
        "version": "0.4",
        "status": "running",
        "memory": "Clinical Working Memory",
    }


def process_request(request: str):
    capability = planner.plan(request)
    context = working_memory.build(request, capability.name)
    experts = dispatcher.build_board(capability)
    opinions = board.discuss(experts)
    result = consensus.build(opinions)
    report = report_builder.build(capability.name, context, result)

    return {
        "capability": capability.name,
        "report": report,
    }


async def runtime_test_request(provider: str = "auto") -> dict:
    response = await ai_runtime.execute(
        provider=provider,
        system_prompt="FHOS AI Runtime health check",
        user_prompt="Return placeholder response",
        temperature=0.2,
    )
    return {
        "status": "ok",
        "provider": response["provider"],
        "runtime": "working",
        "response": response,
    }
