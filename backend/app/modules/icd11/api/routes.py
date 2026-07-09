from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.icd11.application.service import ICD11Service
from app.modules.icd11.schemas.icd11 import ICD11NodeRead

router = APIRouter(prefix="/icd11", tags=["ICD-11"])


@router.get("/nodes", response_model=list[ICD11NodeRead])
def list_children(parent_id: str | None = None, uow: UnitOfWork = Depends(get_uow)):
    """Без parent_id -- кореневі вузли (Chapter, parent_id IS NULL).
    З parent_id -- прямі діти вузла (Block чи Category).
    """
    service = ICD11Service(uow)
    return service.list_children(parent_id)


@router.get("/nodes/{node_id:path}", response_model=ICD11NodeRead)
def get_node(node_id: str, uow: UnitOfWork = Depends(get_uow)):
    """{node_id:path} -- id це WHO Linearization URI, може містити '/'."""
    service = ICD11Service(uow)
    node = service.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ICD-11 вузол з id={node_id!r} не знайдено",
        )
    return node
