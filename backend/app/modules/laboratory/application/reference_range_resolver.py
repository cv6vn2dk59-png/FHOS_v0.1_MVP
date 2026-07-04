from app.application.uow import UnitOfWork
from app.modules.laboratory.domain.reference_range import ReferenceRange
from app.modules.laboratory.persistence import reference_range_mapper as mapper
from app.modules.laboratory.persistence.reference_range_orm import ReferenceRangeORM


class ReferenceRangeResolver:
    """Знаходить найбільш специфічний ReferenceRange для контексту пацієнта.

    Навмисно НЕ залежить від PatientProfileORM чи Profile-модуля — приймає
    лише примітиви (test_code, unit, sex, age, laboratory_name, method).

    НЕ вигадує відсутні дані: якщо sex/age пацієнта невідомі (None),
    розглядаються тільки діапазони без відповідного обмеження. Якщо
    підходящого діапазону немає — повертає None, не fallback "навмання".
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def resolve(
        self,
        *,
        test_code: str,
        unit: str,
        sex: str | None = None,
        age: int | None = None,
        laboratory_name: str | None = None,
        method: str | None = None,
    ) -> ReferenceRange | None:
        repository = self.uow.repo(ReferenceRangeORM)
        candidates_orm = repository.get_candidates(test_code=test_code, unit=unit)
        candidates = [mapper.to_domain(orm) for orm in candidates_orm]

        matching = [
            candidate
            for candidate in candidates
            if candidate.matches(
                test_code=test_code,
                unit=unit,
                sex=sex,
                age=age,
                laboratory_name=laboratory_name,
                method=method,
            )
        ]

        if not matching:
            return None

        max_score = max(candidate.specificity_score() for candidate in matching)
        best_candidates = [c for c in matching if c.specificity_score() == max_score]

        best_candidates.sort(key=lambda c: c.id or 0)
        return best_candidates[0]