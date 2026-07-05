from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.imaging.application.service import ImagingService, InvalidPatientReferenceError
from app.modules.imaging.schemas.imaging import ImagingStudyCreate, ImagingStudyRead

router = APIRouter(prefix="/imaging", tags=["Imaging"])


@router.post("/", response_model=ImagingStudyRead, status_code=status.HTTP_201_CREATED)
def create_study(data: ImagingStudyCreate, uow: UnitOfWork = Depends(get_uow)):
    service = ImagingService(uow)
    try:
        return service.create_study(data)
    except InvalidPatientReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/patient/{patient_profile_id}", response_model=list[ImagingStudyRead])
def list_studies_for_patient(
    patient_profile_id: int,
    study_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ImagingService(uow)
    return service.list_studies_for_patient(patient_profile_id, study_type, skip, limit)