cd D:\FHOS\FHOS_v0.1_MVP
@'
# FHOS S05E02 — Drug Interactions v1 — Implementation Summary

Дата: 2026-07-06
Статус: Vertical Slice завершено. Seed реальних даних у БД — відкладено.

## Реалізовано

1. **Domain** (commit b2e610a)
   - DrugInteraction: side_a/side_b як списки речовин (класи, не окремі
     речовини) - Phansalkar 2013 визначає взаємодії на рівні класів.
   - Symmetry Rule: pair_key() незалежний від порядку side_a/side_b.
   - find_interactions(): пошук серед списку речовин пацієнта.
   - name_mapping.py: локальна таблиця "введена назва -> речовина"
     (ADR-0012 - живе тут до другого підтвердженого споживача).
   - phansalkar_2013.py: 15 реальних взаємодій, факти власними словами
     (не текст статті - джерело під звичайним copyright, не CC BY).
   - 16 unit-тестів.

2. **Persistence** (commit f20f7c0)
   - DrugInteractionORM: side_a/side_b як JSON-колонки.
   - Repository, mapper, реєстрація в model_registry.py.
   - Alembic-міграція 4866a7e4c6ea, застосована.

3. **Application** (commit 23c1205)
   - DrugInteractionService.check_active_medications(): читає активні
     препарати пацієнта з Medications, нормалізує назви, шукає
     взаємодії. Fallback на дані з phansalkar_2013.py в пам'яті, якщо
     таблиця в БД порожня (seed ще не виконано).
   - 4 інтеграційні тести.

4. **API** (commit 070fda3)
   - GET /drug-interactions/patient/{patient_profile_id}/check

## Відкладено (свідомо, не забуто)

- **Seed реальних 15 записів у таблицю drug_interactions** - fallback
  на дані в пам'яті вже покриває функціональність v1. Зробити, коли
  з'явиться реальна потреба редагувати список через БД, а не тільки
  через код (Confirmed Repetition, not Confirmed Intention).
- **Interaction Evidence View (3 блоки: verified/patient_note/
  prescription_history)** - реалізовано лише verified_interaction.
  patient_note і prescription_history - окремі сервіси, коли з'явиться
  конкретний UI-запит.
- **PDF статті Phansalkar 2012** - навмисно НЕ в git (авторське право
  BMJ Publishing, не CC BY). Факти взято зі статті, перекладені
  власними словами в коді, посилання на джерело - в knowledge_source_id.

## Ідея на майбутнє (не архітектурне рішення, тільки нотатка)

Обговорено ідею контрольованого агента (напр. Claude Code) для
механічної роботи (створення файлів, запуск тестів, перевірка) замість
ручного копіювання через чат. Не реалізовано зараз - окрема Architect
Session потрібна для питань доступу і меж контролю.

## Тести
20/20 passed (16 domain + 4 application).

## Наступна робота
- Продовжити Vertical Slice: patient_note, prescription_history
  (Interaction Evidence View), коли з'явиться конкретна потреба.
- Seed script для реальних даних у БД.
- Consistency Review Drug Interactions (за зразком Laboratory) після
  накопичення досвіду використання.
'@ | Set-Content -Path docs\SPRINT_5_E02_SUMMARY.md -Encoding utf8

cd D:\FHOS\FHOS_v0.1_MVP
$addition = @'

## Оновлення (Interaction Evidence View — prescription_history)

Реалізовано другий блок Interaction Evidence View:
- domain: PrescriptionHistoryEntry, find_historical_overlapping_prescriptions()
  (overlap у часі, end_date=None -> триває дотепер) — commit 1f47f1d
- application: DrugInteractionService.find_prescription_history() — commit 9ba63d8
- tests: 3 інтеграційні тести — commit d68b739
- API: GET /drug-interactions/patient/{id}/evidence (verified + prescription_history) — commit b9db677

Усього тестів модуля: 28/28 passed.

patient_note (третій блок Evidence View) — досі свідомо відкладено,
без конкретного запиту на реалізацію.
'@
Add-Content -Path docs\SPRINT_5_E02_SUMMARY.md -Value $addition -Encoding utf89