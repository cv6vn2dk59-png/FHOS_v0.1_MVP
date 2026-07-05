$root = 'D:\FHOS\FHOS_v0.1_MVP'
@'
# Module Development Workflow

Еталонна послідовність, підтверджена на Laboratory + Reference Range (Sprint 3). Використовувати для кожного нового медичного модуля (Imaging, Medications тощо).

## Порядок
1. **Architecture Discussion** — обговорення підходу в чаті, до коду.
2. **Architecture Decision** — явне рішення; цього достатньо для старту коду, Constitution оновлюється пізніше.
3. **Генерація каркасу**: `python tools/create_module.py <module_name>` — автоматично створює ORM (з базовими полями), Domain (каркас), Mapper, Repository (з реєстрацією), Schemas, API routes, тести, і програмно підключає модуль в `app/persistence/model_registry.py` та `app/api/router.py`.
4. **Domain First** — наповнити Domain реальною клінічною логікою (не Anemic Model) ПЕРЕД тим, як розширювати ORM/API.
5. **Unit tests для Domain** — кожен клінічний метод покривається межовими випадками (нормальні значення, відсутні дані, межі діапазонів).
6. **ORM + Alembic migration** — `alembic revision --autogenerate`, звірити згенерований DDL проти очікуваного ПЕРЕД `alembic upgrade head`.
7. **Service + API integration tests** — перевірка повного шляху HTTP → Domain → DB.
8. **Live end-to-end перевірка** — реальний HTTP-запит через uvicorn, не тільки тести.
9. **Retrospective / Devil Review** — незалежна критика (ChatGPT або інша друга думка) РЕАЛІЗОВАНОГО рішення, до фіксації в ADR.
10. **ADR** — тільки для рішень, що змінюють архітектуру, впливають на майбутні модулі, можуть бути переглянуті окремо. Технічні деталі реалізації (bug fixes, patterns) — у Developer Guide, не ADR.
11. **Constitution Update** — коли власник проекту явно підтверджує "Constitution vX.Y Approved".

## Критерій "чи потрібен ADR"
Так: впливає на архітектуру, може вплинути на майбутні модулі, може бути переглянуте окремо.
Ні: implementation pattern, bug fix, технічна деталь без архітектурних наслідків → Common Pitfalls.md або тут.
'@ | Out-File -Encoding utf8 "$root\docs\DEVELOPER_GUIDE\Module Development Workflow.md"