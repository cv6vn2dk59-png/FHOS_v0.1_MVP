import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.application.uow import UnitOfWork
from app.modules.laboratory.application.reference_range_resolver import ReferenceRangeResolver
from app.modules.laboratory.persistence.reference_range_orm import ReferenceRangeORM
from app.persistence.base import Base

import app.modules.laboratory.persistence.reference_range_repository  # noqa: F401


@pytest.fixture
def uow():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return UnitOfWork(session_factory=session_factory)


def seed(session, **overrides):
    defaults = dict(
        test_code="GLU",
        test_name="Glucose",
        unit="mmol/L",
        reference_min=3.9,
        reference_max=5.5,
    )
    defaults.update(overrides)
    row = ReferenceRangeORM(**defaults)
    session.add(row)
    session.commit()
    return row


class TestResolverNotFound:
    def test_returns_none_when_no_candidates_exist(self, uow):
        with uow as active_uow:
            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L")
            assert result is None

    def test_returns_none_when_unit_does_not_match(self, uow):
        with uow as active_uow:
            seed(active_uow.session, unit="mmol/L")
            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mg/dL")
            assert result is None


class TestResolverDefaultMatch:
    def test_returns_default_range_when_no_specific_context(self, uow):
        with uow as active_uow:
            seed(active_uow.session, reference_min=3.9, reference_max=5.5)
            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L")
            assert result is not None
            assert result.reference_min == 3.9
            assert result.is_default() is True


class TestResolverSpecificityPriority:
    def test_sex_specific_range_wins_over_default(self, uow):
        with uow as active_uow:
            seed(active_uow.session, sex=None, reference_min=3.3, reference_max=5.8)
            seed(active_uow.session, sex="female", reference_min=3.5, reference_max=5.5)

            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L", sex="female")

            assert result is not None
            assert result.sex == "female"
            assert result.reference_min == 3.5

    def test_sex_and_age_range_wins_over_sex_only(self, uow):
        with uow as active_uow:
            seed(active_uow.session, sex="male", reference_min=3.9, reference_max=5.5)
            seed(
                active_uow.session,
                sex="male",
                age_min=18,
                age_max=65,
                reference_min=4.0,
                reference_max=5.4,
            )

            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L", sex="male", age=30)

            assert result is not None
            assert result.age_min == 18
            assert result.reference_min == 4.0

    def test_falls_back_to_default_when_context_does_not_match_specific(self, uow):
        with uow as active_uow:
            seed(active_uow.session, sex=None, reference_min=3.3, reference_max=5.8)
            seed(active_uow.session, sex="female", reference_min=3.5, reference_max=5.5)

            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L", sex="male")

            assert result is not None
            assert result.is_default() is True


class TestResolverUnknownContext:
    def test_unknown_sex_only_matches_default_range(self, uow):
        with uow as active_uow:
            seed(active_uow.session, sex=None, reference_min=3.3, reference_max=5.8)
            seed(active_uow.session, sex="male", reference_min=3.9, reference_max=5.5)

            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L", sex=None)

            assert result is not None
            assert result.sex is None


class TestResolverTieBreak:
    def test_deterministic_tie_break_by_id(self, uow):
        with uow as active_uow:
            first = seed(active_uow.session, sex="male", reference_min=3.9, reference_max=5.5)
            seed(active_uow.session, sex="male", reference_min=4.0, reference_max=5.4)

            resolver = ReferenceRangeResolver(active_uow)
            result = resolver.resolve(test_code="GLU", unit="mmol/L", sex="male")

            assert result is not None
            assert result.id == first.id