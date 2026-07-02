from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class PatientProfileCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: date | None = None
    sex: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class PatientProfileRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_date: date | None = None
    sex: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }