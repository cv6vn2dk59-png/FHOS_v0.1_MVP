from fastapi import APIRouter, Depends

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.contraindications.application.service import ContraindicationService
from app.modules.contraindications.schemas.contraindications import (
    ContraindicationCheckResult,
)

router = APIRouter(prefix="/contraindications", tags=["Contraindications"])


@router.get("/patient/{patient_profile_id}", response_model=ContraindicationCheckResult)
def check_patient(
    patient_profile_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    """Відомі протипоказання серед АКТИВНИХ препаратів і АКТИВНИХ хвороб
    пацієнта (ADR-0014 п.4, закриття -- S07E05).

    Немає POST: Contraindication -- read-only knowledge asset із seed,
    той самий підхід, що ICD11NodeRead/GET /icd11/nodes.

    Devil Review S07E07, крок 3: відповідь -- об'єкт, не голий список.
    `coverage_warning` -- СТАТИЧНИЙ текст (однаковий завжди, не рахує
    unmapped-препарати/хвороби -- свідоме обмеження Scope, погоджено з
    власником), що прямо адресує ризик "порожній результат виглядає як
    'протипоказань немає'": normalize_to_chebi()/normalize_to_mondo() --
    exact-match проти навмисно малих словників (4 речовини, 10 хвороб),
    і порожній `contraindications` НЕ є клінічною гарантією.
    """
    service = ContraindicationService(uow)
    contraindications = service.check_patient(patient_profile_id)
    return ContraindicationCheckResult(contraindications=contraindications)
