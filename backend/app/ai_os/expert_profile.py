"""
FHOS AI Operating System

Expert Profile
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ExpertProfile:

    # ---------- Identity ----------

    id: str
    domain: str
    title: str
    version: str = "1.0"

    # ---------- AI ----------

    provider: str = "auto"
    model: str = "auto"

    # ---------- Knowledge ----------

    role: str = ""

    description: str = ""

    competencies: List[str] = field(default_factory=list)

    guidelines: List[str] = field(default_factory=list)

    supported_documents: List[str] = field(default_factory=list)

    supported_modalities: List[str] = field(default_factory=list)

    laboratory_markers: List[str] = field(default_factory=list)

    supported_capabilities: List[str] = field(default_factory=list)

    # ---------- Prompt ----------

    system_prompt: str = ""

    # ---------- Runtime ----------

    priority: str = "normal"

    enabled: bool = True

    confidence_weight: float = 1.0

    # ---------- Metadata ----------

    tags: List[str] = field(default_factory=list)

    metadata: Dict = field(default_factory=dict)