# ADR-0003 — Платформонезалежна архітектура

## Статус
Прийнято.

## Рішення
FHOS має працювати на Windows, Linux і macOS без переписування логіки системи.

## Обраний напрям
- Backend: Python / FastAPI
- Frontend: React / TypeScript
- Desktop: Tauri
- Database: SQLite на старті, PostgreSQL надалі
- Deployment: Docker
