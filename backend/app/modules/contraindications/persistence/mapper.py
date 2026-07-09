from app.modules.contraindications.domain.entities import Contraindication
from app.modules.contraindications.persistence.orm import ContraindicationORM


def to_domain(orm: ContraindicationORM) -> Contraindication:
    return Contraindication(
        id=orm.id,
        substance_chebi_id=orm.substance_chebi_id,
        disease_mondo_id=orm.disease_mondo_id,
        description=orm.description,
        knowledge_source_id=orm.knowledge_source_id,
    )


def to_orm(domain: Contraindication) -> ContraindicationORM:
    return ContraindicationORM(
        substance_chebi_id=domain.substance_chebi_id,
        disease_mondo_id=domain.disease_mondo_id,
        description=domain.description,
        knowledge_source_id=domain.knowledge_source_id,
    )
