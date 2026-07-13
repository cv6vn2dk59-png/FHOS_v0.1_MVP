from sqlalchemy.exc import IntegrityError

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.reference_range_resolver import ReferenceRangeResolver
from app.modules.laboratory.domain.entities import (
    LaboratoryResult,
    ReferenceRangeStatus,
    TrendDirection,
)
from app.modules.laboratory.persistence import mapper
from app.modules.laboratory.persistence.orm import LaboratoryResultORM
from app.modules.laboratory.schemas.laboratory import LaboratoryResultCreate


class LaboratoryResultNotFoundError(Exception):
    """Немає жодного результату для вказаного пацієнта/аналіту."""


class InvalidPatientReferenceError(Exception):
    """patient_profile_id вказує на профіль, якого не існує."""

    def __init__(self, patient_profile_id: int):
        self.patient_profile_id = patient_profile_id
        super().__init__(f"Профіль пацієнта з id={patient_profile_id} не існує")


class LaboratoryService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_result(
        self,
        data: LaboratoryResultCreate,
        sex: str | None = None,
        age: int | None = None,
    ) -> LaboratoryResult:
        reference_min = data.reference_min
        reference_max = data.reference_max

        if reference_min is not None and reference_max is not None:
            reference_range_status = ReferenceRangeStatus.MANUAL
        elif data.test_code is not None and data.unit is not None:
            resolver = ReferenceRangeResolver(self.uow)
            resolved = resolver.resolve(
                test_code=data.test_code,
                unit=data.unit,
                sex=sex,
                age=age,
                laboratory_name=data.laboratory_name,
                method=data.method,
            )
            if resolved is not None:
                reference_min = resolved.reference_min
                reference_max = resolved.reference_max
                reference_range_status = ReferenceRangeStatus.RESOLVED
            else:
                reference_range_status = ReferenceRangeStatus.NOT_FOUND
        else:
            reference_range_status = ReferenceRangeStatus.NOT_FOUND

        domain_result = LaboratoryResult(
            test_name=data.test_name,
            patient_profile_id=data.patient_profile_id,
            test_code=data.test_code,
            value=data.value,
            unit=data.unit,
            reference_min=reference_min,
            reference_max=reference_max,
            reference_text=data.reference_text,
            critical_low=data.critical_low,
            critical_high=data.critical_high,
            result_date=data.result_date,
            laboratory_name=data.laboratory_name,
            notes=data.notes,
            reference_range_status=reference_range_status,
        )

        domain_result.interpret()

        orm_result = mapper.to_orm(domain_result)

        try:
            self.uow.repo(LaboratoryResultORM).add(orm_result)
            self.uow.commit()
        except IntegrityError as exc:
            self.uow.rollback()
            if data.patient_profile_id is not None:
                raise InvalidPatientReferenceError(data.patient_profile_id) from exc
            raise

        return mapper.to_domain(orm_result)

    def list_results_for_patient(
        self,
        patient_profile_id: int,
        test_code: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[LaboratoryResult]:
        repository = self.uow.repo(LaboratoryResultORM)
        orm_results = repository.get_results_for_patient(
            patient_profile_id=patient_profile_id,
            test_code=test_code,
            skip=skip,
            limit=limit,
        )
        return [mapper.to_domain(orm) for orm in orm_results]

    def get_trend(self, patient_profile_id: int, test_code: str) -> tuple[LaboratoryResult, TrendDirection]:
        all_results = self.list_results_for_patient(patient_profile_id, test_code=test_code, limit=1000)

        results_with_date = [r for r in all_results if r.result_date is not None]
        if not results_with_date:
            raise LaboratoryResultNotFoundError(
                f"Немає результатів з result_date для пацієнта {patient_profile_id} по тесту {test_code!r}"
            )

        latest = max(results_with_date, key=lambda r: r.result_date)
        history = [r for r in results_with_date if r is not latest]

        return latest, latest.trend(history)