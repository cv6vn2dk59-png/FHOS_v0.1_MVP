from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    InteractionSeverity,
    PatientInteractionNote,
)
from app.modules.drug_interactions.persistence.orm import (
    DrugInteractionORM,
    InteractionSeverityORM,
    PatientInteractionNoteORM,
)


def to_domain(orm: DrugInteractionORM) -> DrugInteraction:
    return DrugInteraction(
        id=orm.id,
        side_a=list(orm.side_a),
        side_b=list(orm.side_b),
        severity=InteractionSeverity(orm.severity.value),
        description=orm.description,
        knowledge_source_id=orm.knowledge_source_id,
    )


def to_orm(domain: DrugInteraction) -> DrugInteractionORM:
    return DrugInteractionORM(
        side_a=list(domain.side_a),
        side_b=list(domain.side_b),
        severity=InteractionSeverityORM(domain.severity.value),
        description=domain.description,
        knowledge_source_id=domain.knowledge_source_id,
    )


def note_to_domain(orm: PatientInteractionNoteORM) -> PatientInteractionNote:
    return PatientInteractionNote(
        id=orm.id,
        patient_profile_id=orm.patient_profile_id,
        substance_a=orm.substance_a,
        substance_b=orm.substance_b,
        note_text=orm.note_text,
        unverified=orm.unverified,
        created_at=orm.created_at,
    )


def note_to_orm(domain: PatientInteractionNote) -> PatientInteractionNoteORM:
    return PatientInteractionNoteORM(
        patient_profile_id=domain.patient_profile_id,
        substance_a=domain.substance_a,
        substance_b=domain.substance_b,
        note_text=domain.note_text,
        unverified=domain.unverified,
    )
