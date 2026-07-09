from fastapi import APIRouter, Depends

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.contraindications.application.service import ContraindicationService
from app.modules.contraindications.schemas.contraindications import ContraindicationRead

router = APIRouter(prefix="/contraindications", tags=["Contraindications"])


@router.get("/patient/{patient_profile_id}", response_model=list[ContraindicationRead])
def check_patient(
    patient_profile_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    """Відомі протипоказання серед АКТИВНИХ препаратів і АКТИВНИХ хвороб
    пацієнта (ADR-0014 п.4, закриття -- S07E05).

    Немає POST: Contraindication -- read-only knowledge asset із seed,
    той самий підхід, що ICD11NodeRead/GET /icd11/nodes.

    ВАЖЛИВО (задокументовано в ContraindicationService.check_patient()
    docstring, повторюємо тут для читачів API): normalize_to_chebi() і
    normalize_to_mondo() -- exact-match проти навмисно малих словників
    (4 речовини, 10 хвороб). Порожній результат НЕ означає відсутність
    протипоказань -- може означати, що жоден препарат/діагноз пацієнта
    не потрапив у ці малі словники.
    """
    service = ContraindicationService(uow)
    return service.check_patient(patient_profile_id)
