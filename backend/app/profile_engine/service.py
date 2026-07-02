"""
FHOS Profile Engine
Business Logic
"""

from sqlalchemy.orm import Session

from app.profile_engine.models import HealthRecord, Person
from app.profile_engine.schemas import PersonCreate


def profile_status():
    return {
        "модуль": "Profile Engine",
        "версія": "0.3",
        "статус": "працює",
        "модель": "Person → HealthRecord → Events / Observations / Documents",
    }


def create_person(db: Session, payload: PersonCreate):
    person = Person(**payload.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)

    health_record = HealthRecord(person_id=person.id)
    db.add(health_record)
    db.commit()
    db.refresh(person)

    return person


def get_person(db: Session, person_id: int):
    return db.query(Person).filter(Person.id == person_id).first()


def list_persons(db: Session):
    return db.query(Person).all()