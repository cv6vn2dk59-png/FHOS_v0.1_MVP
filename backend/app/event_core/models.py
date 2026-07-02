"""
FHOS Event Model
"""

from enum import Enum


class EventType(str, Enum):

    USER_REQUEST = "user_request"

    LAB_RESULT_RECEIVED = "lab_result_received"

    DOCUMENT_UPLOADED = "document_uploaded"

    IMAGE_UPLOADED = "image_uploaded"

    DEVICE_DATA_RECEIVED = "device_data_received"

    MEDICATION_CHANGED = "medication_changed"

    FOLLOW_UP_DUE = "follow_up_due"

    SYSTEM_EVENT = "system_event"