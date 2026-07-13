# S08E04 — Full Laboratory Profile → Clinical Reasoning Graph

## Implemented

- Added `POST /api/clinical-reasoning/laboratory-profile`.
- Projects every selected laboratory result into the graph; normal results are not filtered out.
- Creates/upserts a `Biomarker` HealthNode and PatientNodeState for every result.
- Adds `laboratory_graph_observations` with a snapshot and provenance back to `laboratory_results.id`.
- Classifies graph observations as signal/context/neutral without treating abnormality as diagnosis.
- Produces review domains for glycemic, lipid, hepatic and renal context.
- Adds a conservative Devil Review requiring trend and clinical context.
- Idempotent projection: repeating the same result does not duplicate graph state.

## Canonical rules

- `normal != irrelevant`
- `abnormal != diagnosis`
- All selected results remain in the returned profile.
- Evidence role in this MVP is profile-level (`signal`, `context`, `neutral`); hypothesis-specific supporting/contradicting roles remain a later step.

## Migration

- `b7c2e5f8a1d` after `d1a4e7c9b2f0`.
