import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.icd11.domain.entities import (
    ICD11Node,
    NodeKind,
    SpecialCode,
    TranslationStatus,
)
from app.modules.icd11.persistence import mapper
from app.modules.icd11.persistence.orm import ICD11NodeORM  # noqa: F401
import app.modules.icd11.persistence.repository  # noqa: F401
from app.persistence.base import Base


@pytest.fixture
def in_memory_uow():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return UnitOfWork(session_factory=session_factory)


def _make(**overrides) -> ICD11Node:
    defaults = dict(
        id="who:chapter-01",
        english_title="Certain infectious or parasitic diseases",
        translation_status=TranslationStatus.VERIFIED,
        node_kind=NodeKind.CHAPTER,
        special_code=SpecialCode.NONE,
        sort_order=1,
        source_release="2024-01",
        parent_id=None,
        icd_code=None,
        ukrainian_title="Певні інфекційні або паразитарні хвороби",
    )
    defaults.update(overrides)
    return ICD11Node(**defaults)


class TestMapperRoundtrip:
    def test_to_orm_then_to_domain_preserves_values(self, in_memory_uow):
        domain = _make()
        with in_memory_uow as uow:
            orm = mapper.to_orm(domain)
            uow.repo(ICD11NodeORM).add(orm)
            uow.commit()

            reloaded = mapper.to_domain(orm)
            assert reloaded.id == "who:chapter-01"
            assert reloaded.node_kind == NodeKind.CHAPTER
            assert reloaded.translation_status == TranslationStatus.VERIFIED
            assert reloaded.special_code == SpecialCode.NONE
            assert reloaded.parent_id is None


class TestSelfReferencingParent:
    def test_child_references_parent_by_id(self, in_memory_uow):
        with in_memory_uow as uow:
            repo = uow.repo(ICD11NodeORM)
            parent = mapper.to_orm(_make(id="who:chapter-01", node_kind=NodeKind.CHAPTER))
            repo.add(parent)
            uow.commit()

            child = mapper.to_orm(_make(
                id="who:block-01",
                node_kind=NodeKind.BLOCK,
                parent_id="who:chapter-01",
                english_title="Block title",
            ))
            repo.add(child)
            uow.commit()

            children = repo.get_children("who:chapter-01")
            assert len(children) == 1
            assert children[0].id == "who:block-01"

    def test_root_node_has_no_children_listed_under_itself(self, in_memory_uow):
        with in_memory_uow as uow:
            repo = uow.repo(ICD11NodeORM)
            repo.add(mapper.to_orm(_make(id="who:chapter-01")))
            uow.commit()

            children = repo.get_children("who:chapter-01")
            assert children == []


class TestRepositoryGetAll:
    def test_get_all_orders_by_sort_order(self, in_memory_uow):
        with in_memory_uow as uow:
            repo = uow.repo(ICD11NodeORM)
            repo.add(mapper.to_orm(_make(id="who:b", sort_order=2)))
            repo.add(mapper.to_orm(_make(id="who:a", sort_order=1)))
            uow.commit()

            all_nodes = repo.get_all()
            assert [n.id for n in all_nodes] == ["who:a", "who:b"]
