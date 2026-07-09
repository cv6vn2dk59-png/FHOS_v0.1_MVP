"""Читання сирого CSV MeDIC Contraindications List у Contraindication.

Шлях до файлу НЕ зашитий у код -- див. MEDIC_DATA_DIR у
resolve_medic_data_dir() чи явний аргумент
load_contraindications_from_csv(). Сирі CSV MeDIC навмисно НЕ
зберігаються в git-репозиторії (розмір, дублювання зовнішнього
джерела -- той самий принцип, що PDF Phansalkar 2012, S05E01/E02).
Постійне місце для будь-яких сирих зовнішніх джерел (не тільки MeDIC):
D:\\FHOS\\external_data\\ (зафіксовано в docs/PROJECT_STATE.md).

Реальний заголовок Contraindications List.csv (перевірено напряму,
2026-07-08) підтверджує очікувану схему (S07E01):
    active ingredient, contraindications, disease contraindicated,
    disease id nameres, disease label nameres, llm_nameres_correct,
    llm disease id, drug id nameres, drug label nameres,
    final normalized disease id, final normalized disease label,
    llm_nameres_correct_drug, llm drug id, final normalized drug id,
    final normalized drug label, drug|disease, is_allergen,
    is_diagnostic_agent
Використовуються лише final normalized drug id / final normalized
disease id / contraindications / llm_nameres_correct /
llm_nameres_correct_drug -- решта колонок ігнорується.
"""
import csv
import os
from pathlib import Path

from app.modules.contraindications.domain.entities import Contraindication

DEFAULT_ENV_VAR = "MEDIC_DATA_DIR"
CONTRAINDICATIONS_FILENAME = "Contraindications List.csv"


def resolve_medic_data_dir(explicit_path: str | None = None) -> Path:
    """Визначає теку з сирими CSV MeDIC.

    Порядок пошуку:
    1. Явно переданий шлях (якщо є).
    2. Змінна середовища MEDIC_DATA_DIR.
    3. Помилка з чітким повідомленням -- НЕ мовчазний fallback на
       шлях всередині репозиторію.
    """
    if explicit_path:
        path = Path(explicit_path)
    else:
        env_value = os.environ.get(DEFAULT_ENV_VAR)
        if not env_value:
            raise RuntimeError(
                f"Шлях до сирих даних MeDIC не заданий. "
                f"Встанови змінну середовища {DEFAULT_ENV_VAR} "
                f'(наприклад: $env:{DEFAULT_ENV_VAR}="D:\\FHOS\\external_data\\medic") '
                f"або передай explicit_path напряму."
            )
        path = Path(env_value)

    if not path.is_dir():
        raise FileNotFoundError(f"Тека з даними MeDIC не знайдена: {path}")

    return path


def load_contraindications_from_csv(
    medic_data_dir: str | None = None,
) -> list[Contraindication]:
    """Читає Contraindications List.csv і повертає список Contraindication.

    Пропускає рядки, де final normalized drug/disease id не мають
    очікуваного CHEBI:/MONDO: префікса (нерозпізнані записи), і рядки,
    де llm_nameres_correct чи llm_nameres_correct_drug явно FALSE
    (низька довіра до LLM-розпізнавання) -- не імпортує сумнівні
    записи мовчки.
    """
    data_dir = resolve_medic_data_dir(medic_data_dir)
    csv_path = data_dir / CONTRAINDICATIONS_FILENAME

    if not csv_path.exists():
        raise FileNotFoundError(f"Файл не знайдено: {csv_path}")

    contraindications: list[Contraindication] = []
    skipped_low_confidence = 0
    skipped_missing_ids = 0

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            drug_id = (row.get("final normalized drug id") or "").strip()
            disease_id = (row.get("final normalized disease id") or "").strip()

            if not drug_id.upper().startswith("CHEBI:") or not disease_id.upper().startswith("MONDO:"):
                skipped_missing_ids += 1
                continue

            drug_ok = (row.get("llm_nameres_correct_drug") or "").strip().upper() != "FALSE"
            disease_ok = (row.get("llm_nameres_correct") or "").strip().upper() != "FALSE"
            if not (drug_ok and disease_ok):
                skipped_low_confidence += 1
                continue

            contraindications.append(
                Contraindication(
                    substance_chebi_id=drug_id,
                    disease_mondo_id=disease_id,
                    description=(row.get("contraindications") or "").strip(),
                    knowledge_source_id="MeDIC_v1",
                )
            )

    print(f"Завантажено: {len(contraindications)} записів")
    print(f"Пропущено (не CHEBI/MONDO): {skipped_missing_ids}")
    print(f"Пропущено (низька довіра LLM): {skipped_low_confidence}")

    return contraindications
