"""
FHOS AI Dispatcher
"""

from enum import Enum


class Agent(Enum):

    GENERAL = "general"

    ENDOCRINOLOGIST = "endocrinologist"

    CARDIOLOGIST = "cardiologist"

    ORTHOPEDIST = "orthopedist"

    TRAUMATOLOGIST = "traumatologist"

    NEUROLOGIST = "neurologist"

    DERMATOLOGIST = "dermatologist"

    GASTROENTEROLOGIST = "gastroenterologist"

    UROLOGIST = "urologist"

    PEDIATRICIAN = "pediatrician"

    NUTRITION = "nutrition"

    FITNESS = "fitness"

    PHARMACOLOGY = "pharmacology"

    LABORATORY = "laboratory"

    RADIOLOGY = "radiology"

    ONCOLOGY = "oncology"