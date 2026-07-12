from fastapi import APIRouter

from app.api.routes_system_db import router as system_db_router
from app.api_core.router import api_router as legacy_api_router
from app.modules.laboratory.api.routes import router as laboratory_router
from app.modules.profile.api.routes import router as profile_router
from app.modules.imaging.api.routes import router as imaging_router
from app.modules.medications.api.routes import router as medications_router
from app.modules.drug_interactions.api.routes import router as drug_interactions_router
from app.modules.diseases.api.routes import router as diseases_router
from app.modules.icd11.api.routes import router as icd11_router
from app.modules.contraindications.api.routes import router as contraindications_router
from app.modules.clinical_reasoning.api.routes import router as clinical_reasoning_router


api_router = APIRouter()

api_router.include_router(system_db_router, tags=["System DB"])
api_router.include_router(profile_router)
api_router.include_router(laboratory_router)
api_router.include_router(imaging_router)
api_router.include_router(medications_router)
api_router.include_router(drug_interactions_router)
api_router.include_router(diseases_router)
api_router.include_router(icd11_router)
api_router.include_router(contraindications_router)
api_router.include_router(clinical_reasoning_router)
api_router.include_router(legacy_api_router)