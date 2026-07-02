"""
FHOS AI Operating System
Service
"""

from app.ai_os.planner import Planner
from app.ai_os.dispatcher import Dispatcher
from app.ai_os.board import MedicalBoard
from app.ai_os.consensus import ConsensusEngine
from app.ai_os.clinical_working_memory import ClinicalWorkingMemory
from app.ai_os.report import ReportBuilder


planner = Planner()
dispatcher = Dispatcher()
board = MedicalBoard()
consensus = ConsensusEngine()
working_memory = ClinicalWorkingMemory()
report_builder = ReportBuilder()


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