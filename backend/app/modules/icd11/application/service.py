from app.application.uow import UnitOfWork
from app.modules.icd11.domain.entities import ICD11Node
from app.modules.icd11.persistence import mapper
from app.modules.icd11.persistence.orm import ICD11NodeORM


class ICD11Service:
    """Read-only доступ до WHO Linearization дерева. Немає create/update
    -- вузли заповнюються importer-ом/seed-скриптом зі статичного
    джерела (ADR-0015), не через цей сервіс.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_node(self, node_id: str) -> ICD11Node | None:
        orm_node = self.uow.repo(ICD11NodeORM).get(node_id)
        if orm_node is None:
            return None
        return mapper.to_domain(orm_node)

    def list_children(self, parent_id: str | None = None) -> list[ICD11Node]:
        orm_nodes = self.uow.repo(ICD11NodeORM).get_children(parent_id)
        return [mapper.to_domain(orm) for orm in orm_nodes]
