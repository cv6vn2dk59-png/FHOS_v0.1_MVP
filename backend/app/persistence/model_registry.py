"""Єдина точка реєстрації всіх ORM-моделей і кастомних Repository-класів.

Навіщо окремо від app/persistence/__init__.py: Base.metadata наповнюється
лише в момент, коли Python РЕАЛЬНО виконує визначення класу ORM-моделі.
Alembic autogenerate порівнює БД з Base.metadata — без імпорту моделі тут
autogenerate вважає, що нових таблиць немає (Sprint 3, Common Pitfalls #3).
RepositoryRegistry.register(...) теж виконується лише в момент імпорту
відповідного persistence/repository.py файлу.

ВАЖЛИВО: тут `import module`, НЕ `from module import Клас`. Простий
`import` не вимагає, щоб клас уже існував у момент виконання рядка —
лише факт виконання файлу. Це розриває цикл, коли якийсь ORM-файл сам
стає першою точкою входу процесу.

Явно імпортується в: alembic/env.py (autogenerate) та app/main.py
(гарантована реєстрація Repository до першого HTTP-запиту).

Кожен новий модуль додає сюди один рядок (ORM) + один рядок (Repository,
якщо кастомний).
"""

import app.modules.profile.persistence.orm  # noqa: F401
import app.modules.laboratory.persistence.orm  # noqa: F401
import app.modules.laboratory.persistence.repository  # noqa: F401
import app.modules.laboratory.persistence.reference_range_orm  # noqa: F401
import app.modules.laboratory.persistence.reference_range_repository  # noqa: F401
import app.modules.imaging.persistence.orm  # noqa: F401
import app.modules.imaging.persistence.repository  # noqa: F401
import app.modules.medications.persistence.orm  # noqa: F401
import app.modules.medications.persistence.repository  # noqa: F401
import app.modules.drug_interactions.persistence.orm  # noqa: F401
import app.modules.drug_interactions.persistence.repository  # noqa: F401
import app.modules.diseases.persistence.orm  # noqa: F401
import app.modules.diseases.persistence.repository  # noqa: F401
import app.modules.contraindications.persistence.orm  # noqa: F401
import app.modules.contraindications.persistence.repository  # noqa: F401
import app.modules.icd11.persistence.orm  # noqa: F401
import app.modules.icd11.persistence.repository  # noqa: F401

import app.modules.clinical_reasoning.persistence.orm  # noqa: F401
import app.modules.clinical_reasoning.persistence.repository  # noqa: F401
