from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.medications.application.service import (
    InvalidPatientReferenceError,
    MedicationService,
)
from app.modules.medications.schemas.medications import MedicationCreate, MedicationRead

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.post("/", response_model=MedicationRead, status_code=status.HTTP_201_CREATED)
def create_medication(data: MedicationCreate, uow: UnitOfWork = Depends(get_uow)):
    service = MedicationService(uow)
    try:
        return service.create_medication(data)
    except InvalidPatientReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/patient/{patient_profile_id}", response_model=list[MedicationRead])
def list_medications_for_patient(
    patient_profile_id: int,
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
):
    service = MedicationService(uow)
    return service.list_medications_for_patient(patient_profile_id, skip, limit)