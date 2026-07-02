"""
Revision helpers
"""

from datetime import datetime

from app.investigation.models import InvestigationRevision


class RevisionFactory:

    @staticmethod
    def first():

        return InvestigationRevision(
            revision=1,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def next(current, event_id=None):

        return InvestigationRevision(
            revision=current.revision + 1,
            created_at=datetime.utcnow(),
            event_id=event_id,
        )