"""Seed-скрипт ICD-11 (WHO SimpleTabulation MMS).

Запуск: python scripts/seed_icd11_data.py
Потребує змінну середовища WHO_ICD11_DATA_DIR (див.
app/modules/icd11/persistence/who_source_loader.py).

Ідемпотентний -- дедуплікація за id напряму (на відміну від
Contraindication/DrugInteraction, тут id -- реальний PK, не
синтетичний DB-серіал, тож дублікат визначається прямим порівнянням
множин).

Обсяг (S07E06, ADR-0015 п.4 закрито): дефолт змінено з розділу 1
(ChapterNo="01", тестова підмножина S07E02) на ПОВНЕ дерево
(chapter_no=None -- усі 26+ глав, ~36000 рядків файлу). Явне рішення
користувача (S07E06), не мовчазна зміна поведінки -- задокументовано
в ADR-0015. Старий режим "лише одна глава" лишається доступним:
`seed(chapter_no="01")`.

flush() після кожного вузла: importer повертає список у порядку
файлу (chapter -> block -> category для КОЖНОЇ глави послідовно),
що природно задовольняє self-referencing FK (батько вже в сесії до
дитини), але ICD11NodeORM не оголошує ORM-рівня relationship() для
parent_id -- SQLAlchemy unit-of-work не має явної інформації про
залежність дитина/батько без цього. flush() per-row робить порядок
insert-ів явним, а не покладається на неявну поведінку session.

Чесне застереження про масштаб: повне дерево -- це ~35000 flush()-ів
замість ~1000 (S07E02). Кожен flush() -- окремий round-trip до БД,
тому очікується помітно довший час виконання (секунди-хвилини, не
миттєво), не помилка. Пакетна оптимізація (flush рідше, за глибиною)
свідомо НЕ зроблена зараз -- Confirmed Repetition: оптимізувати, коли
реальний час виконання виявиться проблемою, не заздалегідь.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.uow import UnitOfWork
from app.modules.icd11.persistence import mapper
from app.modules.icd11.persistence.orm import ICD11NodeORM
from app.modules.icd11.persistence.who_source_loader import load_icd11_chapter_from_xlsx
import app.persistence.model_registry  # noqa: F401


def seed(chapter_no: str | None = None) -> None:
    nodes = load_icd11_chapter_from_xlsx(chapter_no=chapter_no)

    with UnitOfWork() as uow:
        repo = uow.repo(ICD11NodeORM)
        existing_ids = {orm.id for orm in repo.get_all()}

        added = 0
        skipped_duplicate = 0
        for node in nodes:
            if node.id in existing_ids:
                skipped_duplicate += 1
                continue

            uow.session.add(mapper.to_orm(node))
            uow.session.flush()
            existing_ids.add(node.id)
            added += 1

        uow.commit()
        print(f"Прочитано з файлу (після фільтрів importer-а): {len(nodes)}")
        print(f"Додано нових вузлів у БД: {added}")
        print(f"Пропущено (вже в БД): {skipped_duplicate}")


if __name__ == "__main__":
    seed()
