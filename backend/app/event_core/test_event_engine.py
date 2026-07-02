"""
Manual Event Engine Test
"""

from app.event_core.engine import EventEngine
from app.event_core.models import EventType


engine = EventEngine()

event = {
    "type": EventType.USER_REQUEST.value,
    "payload": {
        "text": "У мене болить голова третій день"
    },
}

result = engine.process(event)

print(result)