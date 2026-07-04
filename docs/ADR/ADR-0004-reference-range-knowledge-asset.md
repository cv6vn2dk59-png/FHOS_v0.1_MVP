# ADR-0004 — Reference Range як Knowledge Asset
## Статус
Прийнято.
## Рішення
Reference Range є окремим медичним знанням (Knowledge Asset), а не просто парою чисел у LaboratoryResult. Фізично Reference Range живе всередині модуля Laboratory (окремий bounded context поки не виправданий обсягом), але логічно належить категорії Medical Knowledge, не Laboratory-специфічній бізнес-логіці.
## Наслідки
- LaboratoryResult.reference_min/reference_max надходять одним із трьох шляхів: вручну (reference_range_status=manual), через ReferenceRangeResolver (resolved), або лишаються невідомими (not_found) — система не вигадує відсутні дані.
- Знання зберігається в окремій таблиці reference_ranges із sex/age/method/laboratory специфічністю, не hardcoded у коді.
- Коли з'явиться підтверджена повторюваність інших типів медичних знань (Drug Interactions, Disease Criteria тощо), ці Knowledge Assets можуть бути винесені в окремий Knowledge Layer — але не раніше появи такої повторюваності.
