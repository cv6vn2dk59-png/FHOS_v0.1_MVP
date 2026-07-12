"""Import disease↔phenotype assertions from an HPO phenotype.hpoa file.

Default mode is DRY RUN. Use --commit to write to the configured FHOS DB.
Raw source files remain outside git, for example:
D:\\FHOS\\external_data\\hpo\\phenotype.hpoa
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import csv

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings

settings = get_settings()
from app.modules.clinical_reasoning.persistence.orm import HealthNodeORM, HealthRelationORM


def _first(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value:
            return value.strip()
    return ""


def parse_rows(path: Path, limit: int | None = None):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader((line for line in handle if not line.startswith("#")), delimiter="\t")
        for index, row in enumerate(reader, start=1):
            if limit is not None and index > limit:
                break
            qualifier = _first(row, "qualifier", "Qualifier")
            if qualifier.upper() == "NOT":
                continue
            disease_id = _first(row, "database_id", "DatabaseID", "databaseId")
            disease_label = _first(row, "disease_name", "DiseaseName", "diseaseName")
            hpo_id = _first(row, "hpo_id", "HPO_ID", "hpoId")
            reference = _first(row, "reference", "Reference") or f"HPO phenotype.hpoa row {index}"
            if not disease_id or not disease_label or not hpo_id:
                continue
            yield disease_id, disease_label, hpo_id, reference


def import_file(path: Path, commit: bool, limit: int | None = None) -> dict[str, int]:
    engine = create_engine(settings.database_url)
    counters = {"rows": 0, "nodes_created": 0, "relations_created": 0}
    with Session(engine) as session:
        for disease_id, disease_label, hpo_id, reference in parse_rows(path, limit):
            counters["rows"] += 1
            symptom = session.execute(select(HealthNodeORM).where(HealthNodeORM.external_id == hpo_id)).scalar_one_or_none()
            if symptom is None:
                symptom = HealthNodeORM(external_id=hpo_id, external_source="HPO", label=hpo_id, node_kind="Symptom")
                session.add(symptom)
                counters["nodes_created"] += 1

            disease = session.execute(select(HealthNodeORM).where(HealthNodeORM.external_id == disease_id)).scalar_one_or_none()
            if disease is None:
                disease = HealthNodeORM(
                    external_id=disease_id,
                    external_source=disease_id.split(":", 1)[0],
                    label=disease_label,
                    node_kind="Disease",
                )
                session.add(disease)
                counters["nodes_created"] += 1

            existing = session.execute(
                select(HealthRelationORM).where(
                    HealthRelationORM.from_node_id == hpo_id,
                    HealthRelationORM.to_node_id == disease_id,
                    HealthRelationORM.relation_kind == "can_explain",
                    HealthRelationORM.source_citation == reference,
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    HealthRelationORM(
                        from_node_id=hpo_id,
                        to_node_id=disease_id,
                        relation_kind="can_explain",
                        evidence_level="individual_study",
                        source_citation=reference,
                        is_directed=True,
                    )
                )
                counters["relations_created"] += 1

        if commit:
            session.commit()
        else:
            session.rollback()
    return counters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--commit", action="store_true", help="Write changes; without this flag the script is dry-run")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if not args.path.exists():
        raise SystemExit(f"File not found: {args.path}")
    result = import_file(args.path, commit=args.commit, limit=args.limit)
    print({**result, "mode": "commit" if args.commit else "dry-run"})


if __name__ == "__main__":
    main()
