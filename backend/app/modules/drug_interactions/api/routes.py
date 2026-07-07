from fastapi import APIRouter, Depends

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.drug_interactions.application.service import DrugInteractionService
from app.modules.drug_interactions.schemas.drug_interactions import (
    DrugInteractionCheckRead,
    DrugInteractionRead,
    InteractionEvidenceViewRead,
    PrescriptionHistoryEntryRead,
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


@router.get(
    "/patient/{patient_profile_id}/evidence",
    response_model=InteractionEvidenceViewRead,
)
def get_interaction_evidence_view(
    patient_profile_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    """Interaction Evidence View: об'єднує verified_interactions
    (активні препарати зараз) і prescription_history (уся історія,
    перетин у часі). НЕ включає patient_note (окремий сервіс,
    ще не реалізований).
    """
    service = DrugInteractionService(uow)

    verified = service.check_active_medications(patient_profile_id)
    history = service.find_prescription_history(patient_profile_id)

    return InteractionEvidenceViewRead(
        patient_profile_id=patient_profile_id,
        verified_interactions=[
            DrugInteractionRead(
                side_a=i.side_a,
                side_b=i.side_b,
                severity=i.severity,
                description=i.description,
                knowledge_source_id=i.knowledge_source_id,
            )
            for i in verified
        ],
        prescription_history=[
            PrescriptionHistoryEntryRead(
                medication_a_name=h.medication_a_name,
                medication_b_name=h.medication_b_name,
                substance_a=h.substance_a,
                substance_b=h.substance_b,
                medication_a_start_date=h.medication_a_start_date,
                medication_a_end_date=h.medication_a_end_date,
                medication_b_start_date=h.medication_b_start_date,
                medication_b_end_date=h.medication_b_end_date,
                overlap_start=h.overlap_start,
                overlap_end=h.overlap_end,
                warning=h.warning,
            )
            for h in history
        ],
    )
