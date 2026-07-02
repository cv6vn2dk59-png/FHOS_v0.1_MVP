"""
Capability Registry
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Capability:
    name: str
    required_domains: List[str]
    optional_domains: List[str]
    priority: int = 1


CAPABILITIES = {

    "laboratory_analysis": Capability(
        name="Laboratory Analysis",
        required_domains=["Laboratory", "Internal Medicine"],
        optional_domains=["Endocrinology", "Nutrition", "Pharmacology"],
    ),

    "drug_interaction": Capability(
        name="Drug Interaction",
        required_domains=["Pharmacology"],
        optional_domains=["Cardiology"],
    ),

    "orthopedic_case": Capability(
        name="Orthopedic Case",
        required_domains=["Orthopedics", "Traumatology"],
        optional_domains=["Radiology", "Rehabilitation"],
    ),

}