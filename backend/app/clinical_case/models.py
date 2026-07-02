"""
FHOS Clinical Case Models
"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class ClinicalCase(Base):
    __tablename__ = "clinical_cases"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, nullable=True, index=True)

    title = Column(String, default="")
    workflow_id = Column(String, nullable=True, index=True)
    state = Column(String, default="new", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)