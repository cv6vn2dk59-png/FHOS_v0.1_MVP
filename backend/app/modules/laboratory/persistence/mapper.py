from app.modules.laboratory.domain.entities import LaboratoryInterpretation, LaboratoryResult
from app.modules.laboratory.persistence.orm import LaboratoryInterpretationORM, LaboratoryResultORM


def to_domain(orm: LaboratoryResultORM) -> LaboratoryResult:
    return LaboratoryResult(
        id=orm.id,
        patient_profile_id=orm.patient_profile_id,
        test_name=orm.test_name,
        test_code=orm.test_code,
        value=orm.value,
        unit=orm.unit,
        reference_min=orm.reference_min,
        reference_max=orm.reference_max,
        reference_text=orm.reference_text,
        result_date=orm.result_date,
        laboratory_name=orm.laboratory_name,
        notes=orm.notes,
        interpretation=LaboratoryInterpretation(orm.interpretation.value),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def to_orm(domain: LaboratoryResult) -> LaboratoryResultORM:
    return LaboratoryResultORM(
        patient_profile_id=domain.patient_profile_id,
        test_name=domain.test_name,
        test_code=domain.test_code,
        value=domain.value,
        unit=domain.unit,
        reference_min=domain.reference_min,
        reference_max=domain.reference_max,
        reference_text=domain.reference_text,
        result_date=domain.result_date,
        laboratory_name=domain.laboratory_name,
        notes=domain.notes,
        interpretation=LaboratoryInterpretationORM(domain.interpretation.value),
    )