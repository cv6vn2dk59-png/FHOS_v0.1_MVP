from app.modules.laboratory.domain.reference_range import ReferenceRange
from app.modules.laboratory.persistence.reference_range_orm import ReferenceRangeORM


def to_domain(orm: ReferenceRangeORM) -> ReferenceRange:
    return ReferenceRange(
        id=orm.id,
        test_code=orm.test_code,
        test_name=orm.test_name,
        unit=orm.unit,
        reference_min=orm.reference_min,
        reference_max=orm.reference_max,
        sex=orm.sex,
        age_min=orm.age_min,
        age_max=orm.age_max,
        source=orm.source,
        laboratory_name=orm.laboratory_name,
        method=orm.method,
        is_active=orm.is_active,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def to_orm(domain: ReferenceRange) -> ReferenceRangeORM:
    return ReferenceRangeORM(
        test_code=domain.test_code,
        test_name=domain.test_name,
        unit=domain.unit,
        reference_min=domain.reference_min,
        reference_max=domain.reference_max,
        sex=domain.sex,
        age_min=domain.age_min,
        age_max=domain.age_max,
        source=domain.source,
        laboratory_name=domain.laboratory_name,
        method=domain.method,
        is_active=domain.is_active,
    )