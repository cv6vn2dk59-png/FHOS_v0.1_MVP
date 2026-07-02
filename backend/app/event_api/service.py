"""
FHOS Universal Event API Service
"""

from app.event_core.engine import EventEngine


event_engine = EventEngine()


def process_event(event: dict):
    result = event_engine.process(event)

    return {
        "status": "ok",
        "result": result,
    }