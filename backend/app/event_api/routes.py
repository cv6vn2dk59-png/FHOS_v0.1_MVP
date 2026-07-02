"""
FHOS Universal Event API Routes
"""

from fastapi import APIRouter

from app.event_api.schemas import EventRequest, EventResponse
from app.event_api.service import process_event


router = APIRouter()


@router.post("", response_model=EventResponse)
def create_event(payload: EventRequest):
    return process_event(payload.model_dump())