from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.diseases.application.service import (
    DiseaseService,
    InvalidPatientReferenceError,
)
from app.modules.diseases.schemas.diseases import DiseaseCreate, DiseaseRead

router = APIRouter(prefix="/diseases", tags=["Diseases"])


@router.post("/", response_model=DiseaseRead, status_code=status.HTTP_201_CREATED)
def create_disease(data: DiseaseCreate, uow: UnitOfWork = Depends(get_uow)):
    service = DiseaseService(uow)
    try:
        return service.create_disease(data)
    except InvalidPatientReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/patient/{patient_profile_id}", response_model=list[DiseaseRead])
def list_diseases_for_patient(
    patient_profile_id: int,
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
):
    service = DiseaseService(uow)
    return service.list_diseases_for_patient(patient_profile_id, skip, limit)
