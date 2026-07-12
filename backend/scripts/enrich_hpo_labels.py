import argparse
import sqlite3
from pathlib import Path


def read_hpo_terms(path: Path) -> dict[str, str]:
    terms: dict[str, str] = {}

    current_id = None
    current_name = None
    is_obsolete = False
    in_term = False

    def flush() -> None:
        nonlocal current_id, current_name, is_obsolete
        if current_id and current_name and not is_obsolete:
            terms[current_id] = current_name

    with path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.rstrip("\n")

            if line == "[Term]":
                if in_term:
                    flush()
                in_term = True
                current_id = None
                current_name = None
                is_obsolete = False
                continue

            if line.startswith("[") and line != "[Term]":
                if in_term:
                    flush()
                in_term = False
                continue

            if not in_term:
                continue

            if line.startswith("id: HP:"):
                current_id = line.removeprefix("id: ").strip()
            elif line.startswith("name: "):
                current_name = line.removeprefix("name: ").strip()
            elif line == "is_obsolete: true":
                is_obsolete = True

    if in_term:
        flush()

    return terms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("obo_file")
    parser.add_argument("--db", default="fhos_local.db")
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    obo_path = Path(args.obo_file)
    if not obo_path.exists():
        raise SystemExit(f"File not found: {obo_path}")

    terms = read_hpo_terms(obo_path)
    connection = sqlite3.connect(args.db)

    hpo_rows = connection.execute(
        """
        SELECT id, external_id, label
        FROM health_nodes
        WHERE external_source = 'HPO'
          AND node_kind = 'Symptom'
        """
    ).fetchall()

    updates = []

    for row_id, external_id, current_label in hpo_rows:
        new_label = terms.get(external_id)

        if new_label and new_label != current_label:
            updates.append((new_label, row_id))

    result = {
        "terms_in_obo": len(terms),
        "hpo_nodes_in_database": len(hpo_rows),
        "labels_to_update": len(updates),
        "mode": "commit" if args.commit else "dry-run",
    }

    if args.commit:
        connection.executemany(
            "UPDATE health_nodes SET label = ? WHERE id = ?",
            updates,
        )
        connection.commit()
    else:
        connection.rollback()

    connection.close()
    print(result)


if __name__ == "__main__":
    main()
