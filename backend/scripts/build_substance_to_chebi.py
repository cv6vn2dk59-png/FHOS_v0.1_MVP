"""Одноразовий скрипт (НЕ виконується в runtime importer-ом чи API):
документує й відтворює алгоритм побудови SUBSTANCE_TO_CHEBI у
app/shared/drug_identity/substance_mapping.py з MeDIC Drug List.csv.

Запуск: python scripts/build_substance_to_chebi.py
Потребує MEDIC_DATA_DIR (той самий env var, що seed_medic_data.py).

Алгоритм (S07E03, узгоджено з користувачем):
Для кожної речовини з BRAND_TO_SUBSTANCE.values() шукати рядки, де
drug_name (розбитий по ';', обрізаний, lower) містить ТОЧНИЙ токен,
що дорівнює шуканій назві -- не підрядок. Це навмисно дозволяє
MeDIC-рядкам, що бандлять базову форму й солі в ОДНОМУ полі
(напр. "AMIODARONE HYDROCHLORIDE; AMIODARONE ; AMIODARONE HCL"),
резолвитись через токен "amiodarone" без хибних збігів на кшталт
substring-матчу "warfarin" всередині "warfarin potassium" як
ОКРЕМОГО рядка з іншим curie.

Серед рядків з точним токен-збігом -- перший, чий curie має префікс
CHEBI:. Якщо такого немає -- НЕ вгадувати: друкується попередження,
substance лишається без запису (None), рішення явно за користувачем.

Реальний результат (2026-07-09): warfarin/amiodarone/sertraline
резолвляються однозначно. tranylcypromine -- точний збіг є, але
БЕЗ CHEBI (curie=PUBCHEM.COMPOUND:73417116); єдиний CHEBI-рядок
(CHEBI:9653) -- це "TRANYLCYPROMINE SULPHATE", сіль-форма, що НЕ
проходить точний токен-збіг. Прийняте рішення (Architect-рівня,
S07E03): CHEBI:9653 -- та сама речовина, інших CHEBI-варіантів у
файлі немає -- зафіксовано вручну в substance_mapping.py, а не
автоматично цим скриптом (скрипт для цього випадку явно друкує
попередження, не вирішує сам).
"""
import csv
import os
from pathlib import Path

from app.shared.drug_identity.substance_mapping import BRAND_TO_SUBSTANCE

DEFAULT_ENV_VAR = "MEDIC_DATA_DIR"
FILENAME = "MeDIC Drug List.csv"


def build_substance_to_chebi() -> dict[str, str | None]:
    data_dir = Path(os.environ[DEFAULT_ENV_VAR])
    csv_path = data_dir / FILENAME

    substances = sorted(set(BRAND_TO_SUBSTANCE.values()))
    result: dict[str, str | None] = {}

    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for substance in substances:
        candidates = []
        for row in rows:
            drug_name = row.get("drug_name") or ""
            tokens = [t.strip().lower() for t in drug_name.split(";")]
            if substance in tokens:
                candidates.append(row)

        chebi_candidates = [
            r for r in candidates if (r.get("curie") or "").upper().startswith("CHEBI:")
        ]

        if chebi_candidates:
            chosen = chebi_candidates[0]
            result[substance] = chosen["curie"]
            if len(chebi_candidates) > 1:
                print(
                    f"УВАГА: {substance} -- кілька CHEBI-кандидатів, взято перший: "
                    f"{[r['curie'] for r in chebi_candidates]}"
                )
        else:
            result[substance] = None
            if candidates:
                non_chebi = [r.get("curie") for r in candidates]
                print(
                    f"УВАГА: {substance} -- точний збіг є, але БЕЗ CHEBI "
                    f"(curie: {non_chebi}) -- НЕ вгадую, потрібне явне рішення"
                )
            else:
                print(f"УВАГА: {substance} -- жодного точного збігу в drug_name")

    return result


if __name__ == "__main__":
    result = build_substance_to_chebi()
    print()
    print("=== SUBSTANCE_TO_CHEBI (для звірки з substance_mapping.py) ===")
    for substance, chebi in result.items():
        print(f"    {substance!r}: {chebi!r},")
