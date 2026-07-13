# S08E06 — Clinical Causality Layer

Recovered in this archive because the supplied ZIP was at 290 tests and did not contain the stated S08E06 files.

Implemented domain primitives:

- `PatientFact → FunctionalProcess → BodySystem → Mechanism → ClinicalHypothesis → ClinicalConsequence → MissingEvidence`
- mandatory provenance;
- evidence strength, confidence and context constraints;
- causal paths remain hypotheses and never become diagnoses automatically.

Alembic revision: `f8b3d6a2c1e4`.
