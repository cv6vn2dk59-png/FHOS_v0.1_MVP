# S08E12 — First Non-Laboratory Vertical Slice: Biomechanics

Implemented a hip/lumbar-pelvic-hip vertical slice over the existing hypothesis graph.

## Added
- Structured non-laboratory `BiomechanicalFact` model.
- Ten independent candidate branches: local joint, muscle-tendon, lumbar-radicular, biomechanical load, degenerative, inflammatory, vascular, traumatic, referred pain, and iatrogenic/postoperative.
- Safety-critical branches remain `unsafe_to_close`.
- Unassigned facts remain visible.
- Imaging findings are not promoted to symptom causation or diagnosis.
- Endpoint: `POST /clinical-reasoning/biomechanics/hip-complex`.
- Persistence and Alembic revision `h8d2f6a0e5c7`.

## Invariants
- symptom location != anatomical source
- imaging change != diagnosis
- association != causality
- cluster/branch != diagnosis
- normal imaging does not exclude functional or load-related mechanisms
- safety alternatives remain visible until assessed
