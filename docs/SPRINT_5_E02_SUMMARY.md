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
Add-Content -Path docs\SPRINT_5_E02_SUMMARY.md -Value $addition -Encoding utf8

## Оновлення (Interaction Evidence View — patient_note, третій блок)

Реалізовано останній блок Interaction Evidence View:
- domain: PatientInteractionNote вже існував (MAX_PATIENT_NOTE_LENGTH=2000,
  unverified завжди True, pair_key() для симетричного пошуку) — тести
  в tests/modules/drug_interactions/test_patient_note.py.
- persistence: PatientInteractionNoteORM (таблиця
  patient_interaction_notes, FK на patient_profiles ON DELETE SET NULL),
  note_to_domain()/note_to_orm() у mapper.py, PatientInteractionNoteRepository
  (get_notes_for_patient()) — Alembic-міграція 9a3d7c1f2b6e, down_revision
  4866a7e4c6ea.
- application: DrugInteractionService.create_patient_note() (IntegrityError
  → InvalidPatientReferenceError, той самий патерн, що й Medications),
  DrugInteractionService.list_patient_notes() — 6 інтеграційних тестів
  у tests/modules/drug_interactions/test_patient_note_service.py.
- API: POST /drug-interactions/patient-notes (201, 400 при неіснуючому
  patient_profile_id, 422 при перевищенні ліміту 2000 символів — Pydantic
  Field на межі API, узгоджено з domain-інваріантом). GET
  /drug-interactions/patient/{id}/evidence тепер повертає всі три блоки:
  verified_interactions, prescription_history, patient_notes.

Усього тестів модуля: 28 (попередньо) + 8 (domain, вже існували) + 6
(application) = перевірено окремим прогоном pytest у чистому venv:
18/18 passed (test_patient_note.py, test_patient_note_service.py,
test_service.py). Повний прогін усього модуля (усі файли разом, включно
з test_prescription_history*.py) не виконувався в цій сесії — venv
проєкту недоступний з поточного середовища; чиста перевірка зроблена на
мінімальній копії зачеплених файлів + смоук-тест через FastAPI
TestClient (create → 201, invalid patient_profile_id → 400, note_text
> 2000 → 422, evidence view повертає patient_notes). Рекомендація:
прогнати `python -m pytest tests/ -v` у робочому venv перед комітом,
щоб підтвердити відсутність регресій за межами перевіреного зрізу.

Interaction Evidence View v1 завершено: усі три блоки (verified_interaction,
prescription_history, patient_note) реалізовані.