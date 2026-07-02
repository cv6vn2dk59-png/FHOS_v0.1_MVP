from fastapi import APIRouter, Depends

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.profile.application.service import ProfileService
from app.modules.profile.schemas.profile import PatientProfileCreate, PatientProfileRead


router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/", response_model=PatientProfileRead)
def create_profile(
    data: PatientProfileCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProfileService(uow)
    return service.create_profile(data)


@router.get("/", response_model=list[PatientProfileRead])
def list_profiles(
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProfileService(uow)
    return service.list_profiles()