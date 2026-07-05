from app.modules.medications.domain.entities import Medication
from app.modules.medications.persistence.orm import MedicationORM


def to_domain(orm: MedicationORM) -> Medication:
    return Medication(
        id=orm.id,
        patient_profile_id=orm.patient_profile_id,
        drug_name=orm.drug_name,
        atc_code=orm.atc_code,
        dose_value=orm.dose_value,
        dose_unit=orm.dose_unit,
        dosage_text=orm.dosage_text,
        start_date=orm.start_date,
        end_date=orm.end_date,
        reason=orm.reason,
        notes=orm.notes,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def to_orm(domain: Medication) -> MedicationORM:
    return MedicationORM(
        patient_profile_id=domain.patient_profile_id,
        drug_name=domain.drug_name,
        atc_code=domain.atc_code,
        dose_value=domain.dose_value,
        dose_unit=domain.dose_unit,
        dosage_text=domain.dosage_text,
        start_date=domain.start_date,
        end_date=domain.end_date,
        reason=domain.reason,
        notes=domain.notes,
    )