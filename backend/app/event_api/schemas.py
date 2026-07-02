"""
FHOS Universal Event API Schemas
"""

from typing import Any

from pydantic import BaseModel, Field


class EventRequest(BaseModel):
    type: str = Field(..., description="Тип події")
    payload: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    status: str
    result: dict[str, Any]