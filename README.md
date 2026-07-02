# FHOS v0.1 MVP

**Family Health Operating System (FHOS)** — локальна, українськомовна, платформонезалежна система для зберігання та аналізу медичних даних сім'ї.

## Поточна мета v0.1

Створити перше програмне ядро:

- локальний backend на Python/FastAPI;
- SQLite-база даних;
- базові профілі членів сім'ї;
- зберігання медичних документів;
- базові лабораторні показники;
- API українською логікою та документацією;
- Docker-оточення;
- готовність до Windows / Linux / macOS.

## Принципи

1. Дані належать користувачу.
2. Українська — основна мова.
3. Система працює локально.
4. AI не є обов'язковим.
5. Старі дані не видаляються, а архівуються.
6. Кожен запис має джерело.
7. Excel/PDF — це експорт, не база даних.

## Швидкий старт

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# або .venv\Scripts\activate на Windows

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Після запуску:
- API: http://127.0.0.1:8000
- Документація API: http://127.0.0.1:8000/docs

## Структура

```text
backend/     Python/FastAPI backend
frontend/    майбутній React/TypeScript інтерфейс
desktop/     майбутня Tauri-оболонка
database/    міграції та схема БД
docs/        документація FHOS
storage/     локальні документи та резервні копії
scripts/     службові скрипти
```
