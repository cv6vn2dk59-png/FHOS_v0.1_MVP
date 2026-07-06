from fastapi import APIRouter, Depends

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.drug_interactions.application.service import DrugInteractionService
from app.modules.drug_interactions.schemas.drug_interactions import (
    DrugInteractionCheckRead,
    DrugInteractionRead,
)

router = APIRouter(prefix="/drug-interactions", tags=["Drug Interactions"])


@router.get(
    "/patient/{patient_profile_id}/check",
    response_model=DrugInteractionCheckRead,
)
def check_active_medications(
    patient_profile_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    """Перевіряє відомі взаємодії (Phansalkar 2013) серед препаратів,
    які пацієнт приймає зараз (Medications.is_active() == True).
    """
    service = DrugInteractionService(uow)
    interactions = service.check_active_medications(patient_profile_id)

    return DrugInteractionCheckRead(
        patient_profile_id=patient_profile_id,
        interactions=[
            DrugInteractionRead(
                side_a=i.side_a,
                side_b=i.side_b,
                severity=i.severity,
                description=i.description,
                knowledge_source_id=i.knowledge_source_id,
            )
            for i in interactions
        ],
        has_interactions=len(interactions) > 0,
    )
