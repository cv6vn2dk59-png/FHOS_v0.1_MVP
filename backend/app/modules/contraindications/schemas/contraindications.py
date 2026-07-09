from pydantic import BaseModel, ConfigDict


class ContraindicationRead(BaseModel):
    """Read-only knowledge asset -- немає ContraindicationCreate: записи
    заповнюються через seed зі статичного джерела MeDIC, не через API
    (той самий підхід, що ICD11NodeRead).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int | None
    substance_chebi_id: str
    disease_mondo_id: str
    description: str
    knowledge_source_id: str
