# S08E02 — Clinical Reasoning execution and data bootstrap

## Implemented

1. `POST /api/clinical-reasoning/hypothesis-expansion`
   - Reads only persisted `HealthRelation` records with `relation_kind=can_explain`.
   - Does not invent diagnoses from model memory.
   - Preserves `USER_SUPPLIED` versus `SYSTEM_GENERATED` origin.
   - Returns a diagnostic-boundary disclaimer.

2. Executable Devil Review
   - Runs User Echo Prohibition and Independence checks.
   - Checks source provenance and verification questions.
   - Flags insufficient etiological diversity.
   - Always returns the three mandatory review questions.

3. `scripts/import_phenotype_hpoa.py`
   - Supports the HPO `phenotype.hpoa` TSV shape.
   - Skips negated (`NOT`) assertions.
   - Creates HPO symptom nodes, disease nodes, and sourced `can_explain` edges.
   - Dry-run by default; `--commit` is required to write.
   - Raw source remains outside git.

4. `scripts/seed_jurisdiction_policies.py`
   - Idempotently seeds verified `general_legal_majority` policies for UA and DE.
   - Does not claim medical-consent or digital-consent thresholds.
   - Stores source URI and verification date.

## Validation

- Full suite: `283 passed`.
- FastAPI route registration verified.
- Fresh Alembic database upgraded through `c8e1f4a9b2d7`.
- Jurisdiction seed verified idempotent: first run creates 2, second run creates 0.

## Still deferred

- Actual import cannot be executed without the user's local `phenotype.hpoa` file.
- HPO phenotype labels are IDs unless a separate HPO terms source is provided.
- HPO remains rare/genetic-disease focused and is not a complete general clinical graph.
- Medical-consent and digital-consent jurisdiction rules remain unseeded pending dedicated legal verification.
- Consent UI, CareTransition UI, emergency access, and full audit API remain deferred.
- Symptom Questionnaire and Disease Trajectory View remain deferred.
- Earlier technical debt (`pair_key`, Optional profile typing, large Drug Interactions entities file) remains untouched.
