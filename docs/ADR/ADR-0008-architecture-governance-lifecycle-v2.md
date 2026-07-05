# ADR-0008 — Architecture Governance Lifecycle v2
## Статус
Прийнято. Supersedes ADR-0006.
## Рішення
Architecture Governance Lifecycle доповнюється кроком Retrospective/Devil Review між Validation і ADR: Discussion → Architecture Decision → Implementation → Validation → Retrospective/Devil Review → ADR → Constitution Update → Approved Architecture. Retrospective — незалежний критичний огляд (людиною чи іншим AI у ролі Devil Advocate) уже реалізованого й перевіреного рішення, що виконується до фіксації рішення в ADR, а не після. Ретроспектива Reference Range Resolver (Sprint 3) фактично виявила необхідність ADR-0007 — це підтверджує, що крок дає реальну архітектурну користь, а не є формальністю.
## Наслідки
- ADR не вважається завершеним до проходження явного Retrospective-кроку; ADR, написаний без попереднього Devil Review, вважається неповним циклом.
- Retrospective може призвести до додаткових ADR (як ADR-0007), що уточнюють чи обмежують щойно реалізоване рішення — це очікувана, здорова частина процесу, не ознака поганого планування.
- ADR-0006 залишається дійсним історичним записом свого часу (Discussion → Decision → Implementation → Constitution Update), але замінений цим документом як актуальний опис Governance Lifecycle.
