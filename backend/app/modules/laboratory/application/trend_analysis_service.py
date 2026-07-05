from app.application.uow import UnitOfWork
from app.modules.laboratory.domain.entities import TrendRiskAssessment
from app.modules.laboratory.persistence import mapper
from app.modules.laboratory.persistence.orm import LaboratoryResultORM


class TrendAnalysisService:
    """Аналіз динаміки лабораторних показників у часі.

    Перший use case — assess_trend_risk(). Сервіс навмисно названий
    ширше за перший метод: майбутні сценарії (slope, variability,
    стабілізація) додаються сюди новими методами, без потреби
    створювати паралельний сервіс чи дублювати доступ до repository.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def assess_trend_risk(self, patient_profile_id: int, test_code: str) -> TrendRiskAssessment:
        repository = self.uow.repo(LaboratoryResultORM)
        orm_results = repository.get_results_for_patient(
            patient_profile_id=patient_profile_id,
            test_code=test_code,
            limit=1000,
        )
        results = [mapper.to_domain(orm) for orm in orm_results]

        results_with_date = [r for r in results if r.result_date is not None]
        results_with_date.sort(key=lambda r: r.result_date)

        return TrendRiskAssessment.assess(results_with_date)