from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="INFO",
    )

    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )