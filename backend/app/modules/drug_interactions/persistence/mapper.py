from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    InteractionSeverity,
)
from app.modules.drug_interactions.persistence.orm import (
    DrugInteractionORM,
    InteractionSeverityORM,
)


def to_domain(orm: DrugInteractionORM) -> DrugInteraction:
    return DrugInteraction(
        id=orm.id,
        side_a=list(orm.side_a),
        side_b=list(orm.side_b),
        severity=InteractionSeverity(orm.severity.value),
        description=orm.description,
        knowledge_source_id=orm.knowledge_source_id,
    )


def to_orm(domain: DrugInteraction) -> DrugInteractionORM:
    return DrugInteractionORM(
        side_a=list(domain.side_a),
        side_b=list(domain.side_b),
        severity=InteractionSeverityORM(domain.severity.value),
        description=domain.description,
        knowledge_source_id=domain.knowledge_source_id,
    )
