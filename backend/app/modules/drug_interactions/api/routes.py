from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.drug_interactions.application.service import (
    DrugInteractionService,
    InvalidPatientReferenceError,
)
from app.modules.drug_interactions.schemas.drug_interactions import (
    DrugInteractionCheckRead,
    DrugInteractionRead,
    InteractionEvidenceViewRead,
    PatientInteractionNoteCreate,
    PatientInteractionNoteRead,
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


@router.post(
    "/patient-notes",
    response_model=PatientInteractionNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_note(
    data: PatientInteractionNoteCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    """Interaction Evidence View, блок patient_note: особиста нотатка
    пацієнта про взаємодію двох речовин. НЕ перевірена системою --
    unverified=True в кожній відповіді, ліміт 2000 символів.
    """
    service = DrugInteractionService(uow)
    try:
        note = service.create_patient_note(data)
    except InvalidPatientReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PatientInteractionNoteRead(
        id=note.id,
        patient_profile_id=note.patient_profile_id,
        substance_a=note.substance_a,
        substance_b=note.substance_b,
        note_text=note.note_text,
        unverified=note.unverified,
        created_at=note.created_at,
    )


@router.get(
    "/patient/{patient_profile_id}/evidence",
    response_model=InteractionEvidenceViewRead,
)
def get_interaction_evidence_view(
    patient_profile_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    """Interaction Evidence View: об'єднує всі три блоки довіри --
    verified_interactions (активні препарати зараз), prescription_history
    (уся історія, перетин у часі) і patient_notes (особисті нотатки,
    НЕ перевірені системою).
    """
    service = DrugInteractionService(uow)

    verified = service.check_active_medications(patient_profile_id)
    history = service.find_prescription_history(patient_profile_id)
    notes = service.list_patient_notes(patient_profile_id)

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
        patient_notes=[
            PatientInteractionNoteRead(
                id=n.id,
                patient_profile_id=n.patient_profile_id,
                substance_a=n.substance_a,
                substance_b=n.substance_b,
                note_text=n.note_text,
                unverified=n.unverified,
                created_at=n.created_at,
            )
            for n in notes
        ],
    )
