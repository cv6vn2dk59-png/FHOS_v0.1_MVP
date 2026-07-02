"""
History manager
"""

from datetime import datetime

from app.investigation.models import HistoryEntry


class HistoryManager:

    @staticmethod
    def append(context, action, **metadata):

        context.history.append(

            HistoryEntry(

                revision=context.revision.revision,

                action=action,

                created_at=datetime.utcnow(),

                metadata=metadata,

            )

        )