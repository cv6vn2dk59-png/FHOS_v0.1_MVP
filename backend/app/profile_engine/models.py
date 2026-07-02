"""
FHOS Profile Engine
Universal Lightweight Health Data Model
"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)

    surname = Column(String, default="")
    first_name = Column(String, default="")
    middle_name = Column(String, default="")
    birth_date = Column(String, nullable=True)
    sex = Column(String, nullable=True)

    health_record = relationship(
        "HealthRecord",
        back_populates="person",
        uselist=False,
        cascade="all, delete-orphan",
    )


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), unique=True)

    summary = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    person = relationship("Person", back_populates="health_record")
    events = relationship("HealthEvent", back_populates="health_record")
    observations = relationship("Observation", back_populates="health_record")
    documents = relationship("HealthDocument", back_populates="health_record")


class HealthEvent(Base):
    __tablename__ = "health_events"

    id = Column(Integer, primary_key=True, index=True)
    health_record_id = Column(Integer, ForeignKey("health_records.id"))

    event_date = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    title = Column(String, default="")
    description = Column(Text, nullable=True)
    medical_domain = Column(String, nullable=True)

    health_record = relationship("HealthRecord", back_populates="events")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    health_record_id = Column(Integer, ForeignKey("health_records.id"))

    observation_date = Column(String, nullable=True)
    name = Column(String, default="")
    value_text = Column(String, nullable=True)
    value_number = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    source = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    health_record = relationship("HealthRecord", back_populates="observations")


class HealthDocument(Base):
    __tablename__ = "health_documents"

    id = Column(Integer, primary_key=True, index=True)
    health_record_id = Column(Integer, ForeignKey("health_records.id"))

    document_date = Column(String, nullable=True)
    title = Column(String, default="")
    document_type = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    source = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    health_record = relationship("HealthRecord", back_populates="documents")