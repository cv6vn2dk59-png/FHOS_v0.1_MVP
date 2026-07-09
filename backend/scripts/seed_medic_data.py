"""Одноразовий seed-скрипт Contraindications (MeDIC v1).

Запуск: python scripts/seed_medic_data.py
Потребує змінну середовища MEDIC_DATA_DIR (див.
app/modules/contraindications/persistence/medic_source_loader.py).

Ідемпотентний -- повторний запуск не створює дублікатів. Дедуплікація
за парою (substance_chebi_id, disease_mondo_id) -- НЕ через pair_key(),
на відміну від seed_phansalkar_data.py: Contraindication асиметрична
(ADR-0014), substance і disease завжди у фіксованих ролях, симетрична
пара тут не потрібна.

Обсяг v1 (Architect Session S07E01, підтверджено користувачем
2026-07-09): тільки записи, де і drug, і disease розпізнані в
CHEBI/MONDO -- 1197 з реального Contraindications List.csv.
Профілювання джерела (S07E01): з 7962 рядків -- 3981 повністю
нерозв'язаних, 2165 розв'язаних в інших словниках (RxNorm/PubChem/
UNII/DrugBank для речовин; UMLS/HP/NCIT/EFO/DOID для хвороб), 619
відкинуто через llm_nameres_correct=FALSE, 1197 завантажено.
Розширення словників за межі CHEBI/MONDO -- явно відкладене окреме
рішення (ADR-0014 п.4), не частина цього seed-у.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.uow import UnitOfWork
from app.modules.contraindications.persistence import mapper
from app.modules.contraindications.persistence.medic_source_loader import (
    load_contraindications_from_csv,
)
from app.modules.contraindications.persistence.orm import ContraindicationORM
import app.persistence.model_registry  # noqa: F401


def seed() -> None:
    contraindications = load_contraindications_from_csv()

    with UnitOfWork() as uow:
        repo = uow.repo(ContraindicationORM)
        existing_orm = repo.get_all()
        existing_keys = {
            (orm.substance_chebi_id, orm.disease_mondo_id) for orm in existing_orm
        }

        added = 0
        skipped_duplicate = 0
        for c in contraindications:
            key = (c.substance_chebi_id, c.disease_mondo_id)
            if key in existing_keys:
                skipped_duplicate += 1
                continue

            uow.session.add(mapper.to_orm(c))
            existing_keys.add(key)
            added += 1

        uow.commit()
        print(f"Прочитано з CSV (після фільтрів завантажувача): {len(contraindications)}")
        print(f"Додано нових записів у БД: {added}")
        print(f"Пропущено (вже в БД, дублікат за substance+disease): {skipped_duplicate}")


if __name__ == "__main__":
    seed()
