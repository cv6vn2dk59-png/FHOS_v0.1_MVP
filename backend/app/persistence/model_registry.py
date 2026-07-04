"""Єдина точка реєстрації всіх ORM-моделей і кастомних Repository-класів.

Навіщо окремо від app/persistence/__init__.py: Base.metadata наповнюється
лише в момент, коли Python РЕАЛЬНО виконує визначення класу ORM-моделі.
Alembic autogenerate порівнює БД з Base.metadata — без імпорту моделі тут
autogenerate вважає, що нових таблиць немає (Sprint 3, Знахідка 6).
RepositoryRegistry.register(...) теж виконується лише в момент імпорту
відповідного persistence/repository.py файлу (Sprint 3, Знахідка 7).

ВАЖЛИВО: тут `import module`, НЕ `from module import Клас`. Простий
`import` не вимагає, щоб клас уже існував у момент виконання рядка —
лише факт виконання файлу. Це розриває цикл, коли якийсь ORM-файл сам
стає першою точкою входу процесу.

Кожен новий модуль додає сюди один рядок (ORM) + один рядок (Repository,
якщо кастомний).
"""

import app.modules.profile.persistence.orm  # noqa: F401
import app.modules.laboratory.persistence.orm  # noqa: F401
import app.modules.laboratory.persistence.repository  # noqa: F401
import app.modules.laboratory.persistence.reference_range_orm  # noqa: F401
import app.modules.laboratory.persistence.reference_range_repository  # noqa: F401