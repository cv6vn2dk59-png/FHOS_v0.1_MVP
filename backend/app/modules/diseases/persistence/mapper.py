from app.modules.diseases.domain.entities import Disease
from app.modules.diseases.persistence.orm import DiseaseORM


def to_domain(orm: DiseaseORM) -> Disease:
    return Disease(
        id=orm.id,
        patient_profile_id=orm.patient_profile_id,
        diagnosis_name=orm.diagnosis_name,
        icd_code=orm.icd_code,
        onset_date=orm.onset_date,
        resolved_date=orm.resolved_date,
        notes=orm.notes,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def to_orm(domain: Disease) -> DiseaseORM:
    return DiseaseORM(
        patient_profile_id=domain.patient_profile_id,
        diagnosis_name=domain.diagnosis_name,
        icd_code=domain.icd_code,
        onset_date=domain.onset_date,
        resolved_date=domain.resolved_date,
        notes=domain.notes,
    )
