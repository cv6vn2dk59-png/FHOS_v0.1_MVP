from sqlalchemy.orm import Session

from app.persistence.system import SystemLog
from app.repositories.base import BaseRepository


class SystemLogRepository(BaseRepository[SystemLog]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=SystemLog)