"""Seed verified GENERAL_MAJORITY policies only.

These records do not claim medical-consent or digital-consent thresholds.
They are deliberately separated by policy_type.
"""
from datetime import date
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings

settings = get_settings()
from app.modules.clinical_reasoning.persistence.orm import JurisdictionPolicyORM

POLICIES = [
    {
        "jurisdiction_code": "UA",
        "policy_type": "general_legal_majority",
        "threshold_age": 18,
        "effective_from": date(2004, 1, 1),
        "source_uri": "https://zakon.rada.gov.ua/laws/show/435-15#Text",
        "source_version": "Civil Code of Ukraine, Article 34; verified 2026-07-12",
    },
    {
        "jurisdiction_code": "DE",
        "policy_type": "general_legal_majority",
        "threshold_age": 18,
        "effective_from": date(1975, 1, 1),
        "source_uri": "https://www.gesetze-im-internet.de/bgb/__2.html",
        "source_version": "BGB §2; verified 2026-07-12",
    },
]


def main() -> None:
    engine = create_engine(settings.database_url)
    created = 0
    with Session(engine) as session:
        for data in POLICIES:
            existing = session.execute(
                select(JurisdictionPolicyORM).where(
                    JurisdictionPolicyORM.jurisdiction_code == data["jurisdiction_code"],
                    JurisdictionPolicyORM.policy_type == data["policy_type"],
                    JurisdictionPolicyORM.effective_from == data["effective_from"],
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(JurisdictionPolicyORM(**data))
                created += 1
        session.commit()
    print({"created": created, "total_known": len(POLICIES)})


if __name__ == "__main__":
    main()
