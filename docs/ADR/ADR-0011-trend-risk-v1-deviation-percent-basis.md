# ADR-0011 — Trend Risk v1: Dynamics via deviation_percent(), not abnormality_score() buckets

## Статус
Прийнято.

## Рішення
TrendAnalysisService.assess_trend_risk() обчислює динаміку відхилення лабораторного показника на основі abs(deviation_percent()) останніх трьох результатів, а не abnormality_score(). Первинна пропозиція (використати abnormality_score() як основу) відхилена після перегляду реалізації: abnormality_score() є дискретизованим severity-класифікатором з п'ятьма сходинками (0.0/0.25/0.5/0.75/1.0), що втрачає роздільну здатність по всій шкалі, не лише на межах категорій — послідовність відхилень 12% → 28% → 29% дає однаковий abnormality_score() (0.5) на всіх трьох точках, приховуючи реальний рух. deviation_percent() є canonical неперервною величиною, з якої abnormality_score() сам обчислюється через bucketization; Trend Risk працює на рівні до дискретизації, лишаючи abnormality_score() виключно для UI/API категоризації. Поріг шуму (stable_threshold_percent, дефолт 5.0) перевикористаний з LaboratoryResult.trend() — не введено нової константи.

STABLE/INCREASING_RISK/DECREASING_RISK визначаються через дельти між сусідніми значеннями distance (не абсолютні значення distance) — перша реалізація (перевірка all(d < threshold)) хибно класифікувала хронічно-відхилений, але стабільний показник як UNCLEAR замість STABLE; виявлено провальним тестом до коміту, виправлено на порівняння delta_1/delta_2 з threshold.

## Наслідки
- Будь-яка майбутня Trend-логіка (slope, variability, стабілізація), що додається до TrendAnalysisService, має так само спиратись на deviation_percent() чи інші неперервні величини, не на abnormality_score().
- TrendRisk (INCREASING_RISK/DECREASING_RISK/STABLE/UNCLEAR/INSUFFICIENT_DATA) і TrendDirection (UP/DOWN/STABLE/INSUFFICIENT_DATA, наявний в LaboratoryResult.trend()) — дві окремі концепції з різними enum, що не повинні змішуватись: TrendDirection порівнює з одним попереднім результатом, TrendRisk аналізує динаміку трьох точок через reference range.
- Vertical Slice для Trend Risk v1 включає API-ендпоінт (GET /laboratory/patient/{id}/trend-risk/{test_code}) — сервіс і тести без API-шару не вважаються завершеним зрізом, за принципом Automation ADR/Constitution ("один повністю робочий Vertical Slice" перед подальшою роботою).