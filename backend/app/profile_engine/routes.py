"""
FHOS Profile Engine
API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.profile_engine.schemas import PersonCreate, PersonWithHealthRecordOut
from app.profile_engine.service import (
    create_person,
    get_person,
    list_persons,
    profile_status,
)

router = APIRouter()


@router.get("/status")
def status():
    return profile_status()


@router.post("/person", response_model=PersonWithHealthRecordOut)
def create(payload: PersonCreate, db: Session = Depends(get_db)):
    return create_person(db, payload)


@router.get("/person", response_model=list[PersonWithHealthRecordOut])
def list_all(db: Session = Depends(get_db)):
    return list_persons(db)


@router.get("/person/{person_id}", response_model=PersonWithHealthRecordOut)
def get_one(person_id: int, db: Session = Depends(get_db)):
    person = get_person(db, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Людину не знайдено")
    return person