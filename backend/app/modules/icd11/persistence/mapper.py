from app.modules.icd11.domain.entities import (
    ICD11Node,
    NodeKind,
    SpecialCode,
    TranslationStatus,
)
from app.modules.icd11.persistence.orm import (
    ICD11NodeORM,
    NodeKindORM,
    SpecialCodeORM,
    TranslationStatusORM,
)


def to_domain(orm: ICD11NodeORM) -> ICD11Node:
    return ICD11Node(
        id=orm.id,
        parent_id=orm.parent_id,
        icd_code=orm.icd_code,
        english_title=orm.english_title,
        ukrainian_title=orm.ukrainian_title,
        translation_status=TranslationStatus(orm.translation_status.value),
        node_kind=NodeKind(orm.node_kind.value),
        special_code=SpecialCode(orm.special_code.value),
        sort_order=orm.sort_order,
        source_release=orm.source_release,
    )


def to_orm(domain: ICD11Node) -> ICD11NodeORM:
    return ICD11NodeORM(
        id=domain.id,
        parent_id=domain.parent_id,
        icd_code=domain.icd_code,
        english_title=domain.english_title,
        ukrainian_title=domain.ukrainian_title,
        translation_status=TranslationStatusORM(domain.translation_status.value),
        node_kind=NodeKindORM(domain.node_kind.value),
        special_code=SpecialCodeORM(domain.special_code.value),
        sort_order=domain.sort_order,
        source_release=domain.source_release,
    )
