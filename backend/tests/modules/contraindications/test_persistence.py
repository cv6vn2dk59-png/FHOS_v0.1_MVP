"""Persistence-роундтрип для Contraindication.

Немає application-шару ще (ADR-0014, application/API заблоковані до
рішення про substance/disease мапінг) -- тому це не test_service.py у
звичному сенсі, а мінімальна перевірка ORM + mapper + repository через
реальний UnitOfWork/SQLAlchemy session, без domain-сервісу над ними.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.contraindications.domain.entities import Contraindication
from app.modules.contraindications.persistence import mapper
from app.modules.contraindications.persistence.orm import ContraindicationORM  # noqa: F401
import app.modules.contraindications.persistence.repository  # noqa: F401
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


class TestMapperRoundtrip:
    def test_to_orm_then_to_domain_preserves_values(self, in_memory_uow):
        domain = Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0005148",
            description="Метформін протипоказаний при тяжкій нирковій недостатності",
            knowledge_source_id="MeDIC_v1",
        )
        with in_memory_uow as uow:
            orm = mapper.to_orm(domain)
            uow.repo(ContraindicationORM).add(orm)
            uow.commit()
            assert orm.id is not None

            reloaded = mapper.to_domain(orm)
            assert reloaded.substance_chebi_id == "CHEBI:6801"
            assert reloaded.disease_mondo_id == "MONDO:0005148"
            assert reloaded.description == domain.description
            assert reloaded.knowledge_source_id == "MeDIC_v1"


class TestRepositoryGetAll:
    def test_get_all_returns_persisted_records(self, in_memory_uow):
        with in_memory_uow as uow:
            repo = uow.repo(ContraindicationORM)
            repo.add(mapper.to_orm(Contraindication(
                substance_chebi_id="CHEBI:6801",
                disease_mondo_id="MONDO:0005148",
                description="x",
                knowledge_source_id="MeDIC_v1",
            )))
            repo.add(mapper.to_orm(Contraindication(
                substance_chebi_id="CHEBI:1234",
                disease_mondo_id="MONDO:0007256",
                description="y",
                knowledge_source_id="MeDIC_v1",
            )))
            uow.commit()

            all_records = repo.get_all()
            assert len(all_records) == 2

    def test_get_all_empty_when_no_records(self, in_memory_uow):
        with in_memory_uow as uow:
            repo = uow.repo(ContraindicationORM)
            assert repo.get_all() == []
