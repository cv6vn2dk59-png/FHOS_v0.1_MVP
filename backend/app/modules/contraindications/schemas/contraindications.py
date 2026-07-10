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


# Devil Review, S07E07, ремедіація крок 3 (погоджено з власником: просте
# СТАТИЧНЕ текстове поле, без динамічного підрахунку unmapped-препаратів/
# хвороб -- та логіка визнана зайвим розширенням Scope). Текст завжди
# однаковий, незалежно від результату check_patient() -- саме тому й
# статичний: адресує ризик "порожній результат виглядає як 'усе гаразд'",
# не намагаючись виміряти, наскільки саме результат неповний.
COVERAGE_WARNING = (
    "Перевірка обмежена малими словниками (CHEBI: 4 речовини, "
    "MONDO: 10 хвороб). Порожній результат НЕ означає відсутність "
    "протипоказань -- препарат або діагноз пацієнта міг не потрапити "
    "в жоден зі словників."
)


class ContraindicationCheckResult(BaseModel):
    """Обгортка відповіді GET /contraindications/patient/{id}: список
    знайдених протипоказань + незмінне текстове попередження про межі
    покриття словників (Devil Review S07E07, крок 3)."""

    contraindications: list[ContraindicationRead]
    coverage_warning: str = COVERAGE_WARNING
