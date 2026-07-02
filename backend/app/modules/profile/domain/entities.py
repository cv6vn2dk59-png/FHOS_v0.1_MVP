from dataclasses import dataclass
from datetime import date


@dataclass
class PatientProfile:
    first_name: str
    last_name: str
    birth_date: date | None = None
    sex: str | None = None
    phone: str | None = None
    email: str | None = None