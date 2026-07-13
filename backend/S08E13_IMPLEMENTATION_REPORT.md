# S08E13 — Biomechanical Examination & Functional Provocation

## Scope

S08E13 adds branch-aware interpretation of physical examination and functional provocation findings for the hip/lumbar-pelvic-hip vertical slice.

## Implemented

- `ExaminationFinding` with provenance and context constraints.
- Active/passive ROM, resisted, provocation, palpation, gait, neurological, vascular and functional-task finding kinds.
- Branch-level effects: supporting, weakening, contradicting, non-discriminating and urgency-changing.
- Explicit `MissingExaminationEvidence`; missing/not-performed data are never converted to negative findings.
- Safety escalation for neurological, vascular, traumatic and postoperative findings.
- Branch summaries preserving supporting, weakening, contradiction, non-discriminating, urgency and missing evidence separately.
- API endpoint: `POST /clinical-reasoning/biomechanics/examination`.
- Persistence schema and Alembic revision `i9e3g7b1f6d8`.

## Governance rules

- provocation test ≠ diagnosis
- pain reproduction ≠ confirmed tissue source
- negative test ≠ absolute exclusion
- range-of-motion restriction ≠ cause by itself
- one examination finding must not select treatment

## Verification

- Dedicated S08E13 unit tests.
- Full regression suite must remain green.
