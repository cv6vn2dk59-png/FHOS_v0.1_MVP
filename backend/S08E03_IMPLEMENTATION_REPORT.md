# S08E03 — Explicit Laboratory Critical Limits

## Problem

FHOS previously classified any result whose deviation from a reference boundary was at least 30% as `critical_low` or `critical_high`. This confused mathematical deviation with a clinically verified critical laboratory value.

Example found by the synthetic test:

- triglycerides 2.3 mmol/L;
- upper reference limit 1.7 mmol/L;
- old result: `critical_high`;
- corrected result: `high` unless an explicit analyte-specific critical limit is supplied.

## Implemented

- Removed percentage-based critical classification from `LaboratoryResult.interpret()`.
- Added nullable `critical_low` and `critical_high` fields to domain, schema, ORM, mapper and service.
- Critical interpretation now requires crossing an explicit threshold.
- `deviation_percent()` and `abnormality_score()` remain unchanged and continue to describe magnitude of deviation.
- Added Alembic revision `d1a4e7c9b2f0`.
- Migration normalizes old heuristic `critical_low/high` rows to `low/high` because no verified explicit threshold existed for those historical classifications.
- Added regression coverage for triglycerides 2.3 with upper limit 1.7.

## Rule

A value outside the reference interval is not automatically a critical laboratory value. `critical_low` or `critical_high` requires an explicit analyte-specific threshold from a verified laboratory or clinical source.
