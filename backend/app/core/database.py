from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.persistence.base import Base

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """Вмикає forced enforcement зовнішніх ключів на кожному новому SQLite-з'єднанні.

    SQLite за замовчуванням НЕ форсує FK constraints (включно з ON DELETE
    CASCADE/SET NULL) без явного PRAGMA на кожному Connection — це не
    властивість БД, а властивість конкретного з'єднання, тому вмикати
    потрібно саме тут, а не одноразово.

    На PostgreSQL (основна БД проекту за Constitution) ця команда
    некоректна, тому явно обмежена діалектом sqlite.
    """
    if engine.dialect.name != "sqlite":
        return

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()