from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork

from app.modules.laboratory.application.service import (
    InvalidPatientReferenceError,
    LaboratoryResultNotFoundError,
    LaboratoryService,
)
from app.modules.laboratory.application.trend_analysis_service import TrendAnalysisService
from app.modules.laboratory.schemas.laboratory import (
    LaboratoryResultCreate,
    LaboratoryResultRead,
    LaboratoryTrendRead,
    TrendRiskRead,
)
from app.modules.profile.application.service import ProfileService
from app.shared.dates import calculate_age


router = APIRouter(prefix="/laboratory", tags=["Laboratory"])


@router.post("/", response_model=LaboratoryResultRead, status_code=status.HTTP_201_CREATED)
def create_result(
    data: LaboratoryResultCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    sex: str | None = None
    age: int | None = None

    if data.patient_profile_id is not None:
        profile = ProfileService(uow).get_profile(data.patient_profile_id)
        if profile is not None:
            sex = profile.sex
            if profile.birth_date is not None:
                age = calculate_age(profile.birth_date)

    service = LaboratoryService(uow)
    try:
        return service.create_result(data, sex=sex, age=age)
    except InvalidPatientReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/patient/{patient_profile_id}", response_model=list[LaboratoryResultRead])
def list_results_for_patient(
    patient_profile_id: int,
    test_code: str | None = None,
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
):
    service = LaboratoryService(uow)
    return service.list_results_for_patient(
        patient_profile_id=patient_profile_id,
        test_code=test_code,
        skip=skip,
        limit=limit,
    )


@router.get("/patient/{patient_profile_id}/trend/{test_code}", response_model=LaboratoryTrendRead)
def get_trend(
    patient_profile_id: int,
    test_code: str,
    uow: UnitOfWork = Depends(get_uow),
):
    service = LaboratoryService(uow)
    try:
        latest, trend_direction = service.get_trend(patient_profile_id, test_code)
    except LaboratoryResultNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return LaboratoryTrendRead(
        patient_profile_id=patient_profile_id,
        test_code=test_code,
        latest_value=latest.value,
        latest_interpretation=latest.interpretation,
        trend=trend_direction,
    )
@router.get("/patient/{patient_profile_id}/trend-risk/{test_code}", response_model=TrendRiskRead)
def get_trend_risk(
    patient_profile_id: int,
    test_code: str,
    uow: UnitOfWork = Depends(get_uow),
):
    service = TrendAnalysisService(uow)
    assessment = service.assess_trend_risk(patient_profile_id, test_code)

    return TrendRiskRead(
        patient_profile_id=patient_profile_id,
        test_code=test_code,
        risk=assessment.risk,
        distances=assessment.distances,
    )