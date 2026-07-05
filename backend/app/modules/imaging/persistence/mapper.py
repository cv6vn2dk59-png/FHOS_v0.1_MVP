from app.modules.imaging.domain.entities import ImagingStudy, ImagingStudyType
from app.modules.imaging.persistence.orm import ImagingStudyORM, ImagingStudyTypeORM


def to_domain(orm: ImagingStudyORM) -> ImagingStudy:
    return ImagingStudy(
        id=orm.id,
        patient_profile_id=orm.patient_profile_id,
        study_type=ImagingStudyType(orm.study_type.value),
        body_part=orm.body_part,
        study_date=orm.study_date,
        facility_name=orm.facility_name,
        radiologist_conclusion=orm.radiologist_conclusion,
        image_file_path=orm.image_file_path,
        notes=orm.notes,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def to_orm(domain: ImagingStudy) -> ImagingStudyORM:
    return ImagingStudyORM(
        patient_profile_id=domain.patient_profile_id,
        study_type=ImagingStudyTypeORM(domain.study_type.value),
        body_part=domain.body_part,
        study_date=domain.study_date,
        facility_name=domain.facility_name,
        radiologist_conclusion=domain.radiologist_conclusion,
        image_file_path=domain.image_file_path,
        notes=domain.notes,
    )