"""Одноразовий seed-скрипт взаємодій Phansalkar et al., 2013.

Запуск: python scripts/seed_phansalkar_data.py
Ідемпотентний -- повторний запуск не створює дублікатів. Дублікати
визначаються через DrugInteraction.pair_key() (симетрична пара
нормалізованих речовин), а не через SQL-рівність JSON-колонок side_a/
side_b -- порядок речовин у списку чи порядок side_a/side_b міг би дати
той самий факт взаємодії у двох різних текстових формах.

Після цього seed-у DrugInteractionService._load_known_interactions()
читає дані з таблиці drug_interactions замість fallback на
PHANSALKAR_2013_INTERACTIONS у пам'яті (docs/SPRINT_5_E02_SUMMARY.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.uow import UnitOfWork
from app.modules.drug_interactions.domain.phansalkar_2013 import (
    PHANSALKAR_2013_INTERACTIONS,
)
from app.modules.drug_interactions.persistence import mapper
from app.modules.drug_interactions.persistence.orm import DrugInteractionORM
import app.persistence.model_registry  # noqa: F401


def seed() -> None:
    with UnitOfWork() as uow:
        repo = uow.repo(DrugInteractionORM)
        existing_orm = repo.get_all()
        existing_keys = {mapper.to_domain(orm).pair_key() for orm in existing_orm}

        added = 0
        for interaction in PHANSALKAR_2013_INTERACTIONS:
            key = interaction.pair_key()
            if key in existing_keys:
                print(f"SKIP (вже існує): {interaction.side_a} <-> {interaction.side_b}")
                continue

            uow.session.add(mapper.to_orm(interaction))
            existing_keys.add(key)
            added += 1
            print(f"OK: додано {interaction.side_a} <-> {interaction.side_b}")

        uow.commit()
        print(f"\nУсього додано нових записів: {added}")


if __name__ == "__main__":
    seed()
