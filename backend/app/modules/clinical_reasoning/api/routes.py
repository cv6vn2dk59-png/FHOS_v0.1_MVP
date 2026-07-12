from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.service import FamilyDataAccessService
from app.modules.clinical_reasoning.schemas.access import ConsentCreate, ConsentRead, SharedNodeRead, SharedNodeRequest

router = APIRouter(prefix="/clinical-reasoning", tags=["Clinical Reasoning"])


@router.post("/family-consents", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
def create_consent(data: ConsentCreate, uow: UnitOfWork = Depends(get_uow)):
    return FamilyDataAccessService(uow).create_consent(**data.model_dump())


@router.post("/family-consents/{consent_id}/revoke", response_model=ConsentRead)
def revoke_consent(consent_id: int, uow: UnitOfWork = Depends(get_uow)):
    try:
        return FamilyDataAccessService(uow).revoke_consent(consent_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/family/shared-nodes", response_model=SharedNodeRead)
def shared_nodes(data: SharedNodeRequest, uow: UnitOfWork = Depends(get_uow)):
    result = FamilyDataAccessService(uow).authorized_shared_nodes(data.actor_id, data.patient_ids, data.purpose_code)
    return {"shared_nodes": result}
