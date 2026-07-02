"""
FHOS Profile Engine
Schemas
"""

from typing import Optional, List
from pydantic import BaseModel


class PersonCreate(BaseModel):
    surname: str = ""
    first_name: str = ""
    middle_name: str = ""
    birth_date: Optional[str] = None
    sex: Optional[str] = None


class PersonOut(PersonCreate):
    id: int

    class Config:
        from_attributes = True


class HealthRecordOut(BaseModel):
    id: int
    person_id: int
    summary: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PersonWithHealthRecordOut(PersonOut):
    health_record: Optional[HealthRecordOut] = None